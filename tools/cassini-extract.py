#!/usr/bin/env python3
"""Reference decoder for Cassini portable meeting files (.opus).

Reads the OpusTags of a portable meeting file and reconstructs the embedded
manifest, and optionally a transcript body, without any Cassini-specific
library. It follows only what the tags themselves declare, so it doubles as a
check that a producer's file is genuinely self-describing.

Handles the published format, and the draft shape that inlined its transcript
sets). Verifies every declared payload SHA-256 and byte count. It does NOT
verify the audio digest — that is tools/cassini-opus-digest.py, which needs no
external tool at all.

Requires ffprobe on PATH. For a reader with no external dependencies see
tools/cassini-read-pure.py.

Usage:
  cassini-extract.py FILE                 # print the manifest as JSON
  cassini-extract.py FILE --tags          # print the raw Cassini descriptor tags
  cassini-extract.py FILE --list          # list transcript ids in a v2/v3 file
  cassini-extract.py FILE --transcript    # print the DEFAULT transcript body
  cassini-extract.py FILE --transcript ID # print one transcript body as JSON
  cassini-extract.py FILE --check         # decode and verify every chunk set

SPDX-License-Identifier: CC0-1.0
"""

import argparse
import base64
import binascii
import gzip
import hashlib
import json
import os
import subprocess
import sys
import zlib

SUPPORTED_ENCODINGS = {"base64url+gzip+utf8json"}
KNOWN_FORMATS = {
    "org.cassini.portable-meeting/1",
    "org.cassini.portable-meeting/2",
    "org.cassini.portable-meeting/1",
}


class CassiniError(Exception):
    """A file-level problem the caller should report, not a crash."""


class PlainAudio(Exception):
    """The file carries no CASSINI_FORMAT tag: it is ordinary Opus audio."""


def read_tags(path):
    """Return the OpusTags of an Ogg Opus file, keys upper-cased.

    OpusTags belong to the Opus logical stream, so ffprobe reports them under
    the stream rather than the format for a plain .opus file. Some remuxes
    surface them at format level instead, so read both and merge, with the
    stream winning on the rare key that appears in both.
    """
    try:
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format_tags:stream_tags",
             "-of", "json", path],
            check=True, capture_output=True, text=True,
        )
    except FileNotFoundError:
        raise CassiniError("ffprobe is not on PATH; this tool needs it to read tags")
    except subprocess.CalledProcessError as exc:
        # A damaged container fails here, before any Cassini rule applies.
        detail = (exc.stderr or "").strip().splitlines()
        raise CassiniError(
            "ffprobe could not read this file"
            + (f": {detail[-1]}" if detail else "")
        )

    try:
        probe = json.loads(probe.stdout)
    except json.JSONDecodeError:
        raise CassiniError("ffprobe returned something that is not JSON")

    tags = {}
    tags.update(probe.get("format", {}).get("tags", {}))
    for stream in probe.get("streams", []):
        tags.update(stream.get("tags", {}))
    return {k.upper(): v for k, v in tags.items()}


def tag_int(tags, key, required=True):
    """Parse an integer tag, refusing ffprobe's duplicate-joining artefact.

    Vorbis allows a field name to appear more than once; ffprobe joins the
    values with ';'. That is unrecoverable here, so say so rather than dying
    inside int().
    """
    raw = tags.get(key)
    if raw is None or raw.strip() == "":
        if required:
            raise CassiniError(f"{key} missing")
        return None
    if ";" in raw:
        raise CassiniError(
            f"{key} appears more than once in OpusTags (ffprobe joined the "
            f"values as {raw!r}); a Cassini file must not repeat a field name"
        )
    try:
        return int(raw.strip())
    except ValueError:
        raise CassiniError(f"{key} is not an integer: {raw!r}") from None


def decode_chunks(tags, prefix, count, encoding, expect_sha256=None,
                  expect_raw=None, expect_gzip=None):
    """Concatenate PREFIX_000..N-1, then undo the declared encoding."""
    if encoding not in SUPPORTED_ENCODINGS:
        raise CassiniError(f"unsupported payload encoding: {encoding!r}")

    parts = []
    for i in range(count):
        key = f"{prefix}{i:03d}"
        if key not in tags:
            raise CassiniError(f"missing payload chunk {key}")
        parts.append(tags[key])
    # A Vorbis comment value is arbitrary UTF-8 and may legally contain
    # whitespace. Go's encoding/base64 skips \r and \n, so the reference
    # reader accepts a wrapped chunk; drop whitespace here for parity.
    b64 = "".join("".join(parts).split())

    # base64url, written unpadded by the reference producer (Go's
    # RawURLEncoding). Re-pad before decoding; accept an already-padded file.
    try:
        raw = base64.urlsafe_b64decode(b64.rstrip("=") + "=" * (-len(b64.rstrip("=")) % 4))
    except (binascii.Error, ValueError) as exc:
        raise CassiniError(f"{prefix}*: base64url decode failed: {exc}") from None

    if expect_gzip is not None and len(raw) != expect_gzip:
        raise CassiniError(
            f"{prefix}*: gzip byte count mismatch: declared {expect_gzip}, got {len(raw)}"
        )
    try:
        body = gzip.decompress(raw)
    except (OSError, EOFError, zlib.error) as exc:
        # zlib.error is not an OSError. A corrupted payload lands here, and the
        # spec says a malformed payload is damaged metadata over valid audio,
        # not a crash.
        raise CassiniError(f"{prefix}*: gzip decompress failed: {exc}") from None

    if expect_raw is not None and len(body) != expect_raw:
        raise CassiniError(
            f"{prefix}*: raw byte count mismatch: declared {expect_raw}, got {len(body)}"
        )
    if expect_sha256:
        got = hashlib.sha256(body).hexdigest()
        if got != expect_sha256.lower():
            raise CassiniError(
                f"{prefix}*: payload sha256 mismatch: declared {expect_sha256}, got {got}"
            )
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CassiniError(f"{prefix}*: payload is not UTF-8 JSON: {exc}") from None


def load_manifest(tags):
    fmt = (tags.get("CASSINI_FORMAT") or "").strip()
    if not fmt:
        # SPEC.md: "If CASSINI_FORMAT is absent, consumers MUST treat the file
        # as plain audio." Not an error; there is simply nothing to extract.
        raise PlainAudio()
    if fmt.lower() not in KNOWN_FORMATS:
        print(f"warning: unknown CASSINI_FORMAT {fmt!r}; decoding anyway",
              file=sys.stderr)

    manifest = decode_chunks(
        tags,
        prefix="CASSINI_PAYLOAD_",
        count=tag_int(tags, "CASSINI_PAYLOAD_CHUNK_COUNT"),
        encoding=tags.get("CASSINI_PAYLOAD_ENCODING", ""),
        expect_sha256=tags.get("CASSINI_PAYLOAD_SHA256"),
        expect_raw=tag_int(tags, "CASSINI_PAYLOAD_RAW_BYTES", required=False),
        expect_gzip=tag_int(tags, "CASSINI_PAYLOAD_GZIP_BYTES", required=False),
    )
    kind = manifest.get("kind")
    if kind != "cassini-portable-meeting":
        raise CassiniError(f"manifest kind is {kind!r}, not 'cassini-portable-meeting'")
    return manifest


def transcript_entries(manifest):
    """The transcript index: transcripts plus any readable ones beside them.

    A published manifest always carries `transcripts`. The inline-`transcript`
    shape belonged to a pre-publication draft that never left the project, and
    the draft reused the identifier this version now uses, so presence of the
    array is what tells them apart rather than the version number.
    """
    entries = list(manifest.get("transcripts", [])) + list(
        manifest.get("readableTranscripts", [])
    )
    if entries:
        return entries
    # A draft-shaped manifest. Adapt it so its content is still reachable.
    out = []
    for key, role in (("transcript", "raw-asr"),
                      ("readableTranscript", "readable-cleanup"),
                      ("displayTranscript", "display")):
        body = manifest.get(key)
        if body:
            out.append({"id": key, "role": role, "inline": True,
                        "wordCount": body.get("wordCount")})
    return out


def default_transcript_id(tags, manifest):
    """Resolve which transcript a viewer should show.

    SPEC.md: the manifest is the record and the tags are the copy, so the
    manifest's `default: true` wins. CASSINI_TRANSCRIPT_DEFAULT is the cheap
    copy for tools that have not decoded the payload yet; a disagreement is
    worth reporting because the reference Go reader prefers the tag and will
    therefore show a different transcript.
    """
    entries = transcript_entries(manifest)
    if not entries:
        return None
    flagged = next((e.get("id") for e in entries if e.get("default")), None)
    tagged = (tags.get("CASSINI_TRANSCRIPT_DEFAULT") or "").strip() or None
    if flagged and tagged and flagged != tagged:
        print(f"warning: CASSINI_TRANSCRIPT_DEFAULT={tagged!r} disagrees with the "
              f"manifest default {flagged!r}; believing the manifest",
              file=sys.stderr)
    return flagged or tagged or entries[0].get("id")


def load_transcript(tags, manifest, wanted):
    for entry in transcript_entries(manifest):
        if entry.get("id") != wanted:
            continue
        if entry.get("inline"):
            # v1 keeps the body inside the manifest itself, under its own
            # top-level key, so there is nothing to decode.
            return manifest[wanted]
        ref = entry.get("payloadRef") or {}
        return decode_chunks(
            tags,
            prefix=ref["prefix"],
            count=int(ref["chunkCount"]),
            encoding=ref.get("encoding", ""),
            expect_sha256=ref.get("sha256"),
            expect_raw=ref.get("rawBytes"),
            expect_gzip=ref.get("gzipBytes"),
        )
    ids = ", ".join(e.get("id", "?") for e in transcript_entries(manifest))
    raise CassiniError(f"no transcript {wanted!r} in this file (have: {ids})")


def run(args):
    tags = read_tags(args.file)

    if args.tags:
        for k in sorted(tags):
            if not k.startswith("CASSINI_"):
                continue
            v = tags[k]
            # payload chunks are long and uninteresting to read
            if "PAYLOAD_" in k and k.rsplit("_", 1)[-1].isdigit():
                v = f"<{len(v)} base64url characters>"
            print(f"{k}={v}")
        return

    manifest = load_manifest(tags)
    default_id = default_transcript_id(tags, manifest)

    if args.list:
        for entry in transcript_entries(manifest):
            flags = " (default)" if entry.get("id") == default_id else ""
            words = entry.get("wordCount")
            words = f"{words} words" if words is not None else "? words"
            print(f"{entry.get('id')}\t{entry.get('role', '?')}\t{words}{flags}")
        return

    if args.check:
        print(f"manifest\tok\tkind={manifest.get('kind')} "
              f"version={manifest.get('version')} profile={manifest.get('profile')}")
        for entry in transcript_entries(manifest):
            body = load_transcript(tags, manifest, entry["id"])
            print(f"{entry['id']}\tok\t{len(body.get('items', []))} items")
        print("all declared sha256 and byte counts match")
        return

    if args.transcript is not None:
        wanted = args.transcript or default_id
        if wanted is None:
            raise CassiniError("this file declares no transcripts")
        body = load_transcript(tags, manifest, wanted)
    else:
        body = manifest

    json.dump(body, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--tags", action="store_true",
                    help="print the Cassini descriptor tags instead of the manifest")
    ap.add_argument("--list", action="store_true",
                    help="list the transcript ids this file carries")
    ap.add_argument("--check", action="store_true",
                    help="decode every chunk set and verify its sha256 and byte counts")
    ap.add_argument("--transcript", metavar="ID", nargs="?", const="",
                    help="print the named transcript body (or the default one)")
    args = ap.parse_args()

    try:
        run(args)
    except PlainAudio:
        print(f"{args.file}: plain audio (no CASSINI_FORMAT tag)", file=sys.stderr)
        return 0
    except CassiniError as exc:
        print(f"{args.file}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        # someone closed the pipe, e.g. `| head`. Redirect stdout to devnull so
        # the interpreter's final flush cannot raise a second time.
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        sys.exit(0)
