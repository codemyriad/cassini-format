#!/usr/bin/env python3
"""Reference decoder for Cassini portable meeting files (.opus).

Reads the OpusTags of a portable meeting file and reconstructs the embedded
manifest, and optionally a transcript body, without any Cassini-specific
library. It follows only what the tags themselves declare, so it doubles as a
check that a producer's file is genuinely self-describing.

Verifies every declared payload SHA-256 and byte count. It does NOT verify the
audio digest — that is tools/cassini-opus-digest.py, which needs no external
tool at all. It also cannot see a repeated tag name: ffprobe folds duplicates
into one value, so that check is left to a reader that parses OpusTags itself,
such as tools/cassini-read-pure.py.

Requires ffprobe on PATH.

Usage:
  cassini-extract.py FILE                 # print the manifest as JSON
  cassini-extract.py FILE --tags          # print the raw Cassini descriptor tags
  cassini-extract.py FILE --list          # list transcript ids in a file
  cassini-extract.py FILE --transcript    # print the DEFAULT transcript body
  cassini-extract.py FILE --transcript ID # print one transcript body as JSON
  cassini-extract.py FILE --check         # decode and verify every chunk set

SPDX-License-Identifier: CC0-1.0
"""

import argparse
import base64
import binascii
import hashlib
import json
import os
import subprocess
import sys
import zlib

SUPPORTED_ENCODINGS = {"base64url+gzip+utf8json"}
KNOWN_FORMATS = {"org.cassini.portable-meeting/1"}
INFLATE_CEILING = 64 << 20   # a chunk set never legitimately inflates past this


class CassiniError(Exception):
    """A file-level problem the caller should report, not a crash."""


class PlainAudio(Exception):
    """The file carries no CASSINI_FORMAT tag: it is ordinary Opus audio."""


class DuplicateTag(CassiniError):
    """A load-bearing CASSINI_* tag appears twice. ffprobe joins repeated
    comments with ';', a byte no base64url chunk or hex digest can contain, so
    for those tags the join is proof of the repeat. The file is
    invalid-cassini-metadata."""


class UnknownFormat(CassiniError):
    """CASSINI_FORMAT names a major version this tool does not implement.

    The state is unknown-cassini-format: play the audio, present no transcript.
    """


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
        if ";" in tags[key]:
            raise DuplicateTag(f"repeated tag {key}")
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
    # Inflate no further than the declared size, and never past the ceiling:
    # the declared value is untrusted and a small payload can inflate to
    # gigabytes. Overrun is a mismatch, not a crash.
    limit = min(expect_raw if expect_raw is not None else INFLATE_CEILING, INFLATE_CEILING)
    try:
        inflater = zlib.decompressobj(16 + zlib.MAX_WBITS)
        body = inflater.decompress(raw, limit + 1)
        if not inflater.eof and not inflater.unconsumed_tail and len(body) <= limit:
            raise CassiniError(f"{prefix}*: gzip stream is truncated")
        if inflater.unused_data:
            raise CassiniError(f"{prefix}*: bytes follow the gzip stream")
    except zlib.error as exc:
        # A corrupted payload lands here, and the spec says a malformed
        # payload is damaged metadata over valid audio, not a crash.
        raise CassiniError(f"{prefix}*: gzip decompress failed: {exc}") from None
    if len(body) > limit:
        raise CassiniError(
            f"{prefix}*: payload inflates past {limit} bytes; "
            f"declared {expect_raw if expect_raw is not None else 'nothing'}"
        )

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
        raise UnknownFormat(
            f"unknown-cassini-format: CASSINI_FORMAT is {fmt!r}; this tool "
            f"implements org.cassini.portable-meeting/1 only, so it presents "
            f"no transcript. The audio still plays."
        )

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
    """Supported bodies: words, then displays. Unknown readable roles are skipped.
    Default selection uses only words; see default_transcript_id."""
    return list(manifest.get("transcripts") or []) + list(
        e for e in manifest.get("readableTranscripts") or []
        if e.get("role") == "display")


def default_transcript_id(tags, manifest):
    """Resolve the words slot: the first `transcripts[]` entry flagged default,
    else the first entry. Array order is normative. CASSINI_TRANSCRIPT_DEFAULT
    is a copy, so it never decides; a disagreement is reported."""
    entries = list(manifest.get("transcripts") or [])
    if not entries:
        return None
    chosen = next((e.get("id") for e in entries if e.get("default")), None) \
        or entries[0].get("id")
    tagged = (tags.get("CASSINI_TRANSCRIPT_DEFAULT") or "").strip() or None
    if tagged and tagged != chosen:
        print(f"warning: CASSINI_TRANSCRIPT_DEFAULT={tagged!r} disagrees with the "
              f"manifest's resolution {chosen!r}; believing the manifest",
              file=sys.stderr)
    return chosen


def load_transcript(tags, manifest, wanted):
    for entry in transcript_entries(manifest):
        if entry.get("id") != wanted:
            continue
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
            print(f"{entry.get('id')}\t{entry.get('format', '?')}\t{words}{flags}")
        return

    if args.check:
        print(f"manifest\tok\tkind={manifest.get('kind')} "
              f"version={manifest.get('version')} profile={manifest.get('profile')}")
        entries = transcript_entries(manifest)
        for entry in entries:
            body = load_transcript(tags, manifest, entry["id"])
            print(f"{entry['id']}\tok\t{len(body.get('items', []))} items")
        print(f"checked: the manifest and {len(entries)} transcript payload(s), "
              f"sha256 and byte counts. Not checked: the audio digest "
              f"(tools/cassini-opus-digest.py).")
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
    except UnknownFormat as exc:
        print(f"{args.file}: {exc}", file=sys.stderr)
        return 2
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
