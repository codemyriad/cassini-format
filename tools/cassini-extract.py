#!/usr/bin/env python3
"""Reference decoder for Cassini portable meeting files (.opus).

Reads the OpusTags of a portable meeting file and reconstructs the embedded
manifest, and optionally a transcript body, without any Cassini-specific
library. It follows only what the tags themselves declare, so it doubles as a
check that a producer's file is genuinely self-describing.

Requires ffprobe on PATH.

Usage:
  cassini-extract.py FILE                 # print the manifest as JSON
  cassini-extract.py FILE --tags          # print the raw Cassini descriptor tags
  cassini-extract.py FILE --list          # list transcript ids in a v2/v3 file
  cassini-extract.py FILE --transcript ID # print one transcript body as JSON
"""

import argparse
import base64
import gzip
import hashlib
import json
import subprocess
import sys

SUPPORTED_ENCODINGS = {"base64url+gzip+utf8json"}


def read_tags(path):
    """Return the OpusTags of an Ogg Opus file, keys upper-cased.

    OpusTags belong to the Opus logical stream, so ffprobe reports them under
    the stream rather than the format for a plain .opus file. Some remuxes
    surface them at format level instead, so read both and merge, with the
    stream winning on the rare key that appears in both.
    """
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format_tags:stream_tags",
         "-of", "json", path],
        check=True, capture_output=True, text=True,
    ).stdout
    probe = json.loads(out)

    tags = {}
    tags.update(probe.get("format", {}).get("tags", {}))
    for stream in probe.get("streams", []):
        tags.update(stream.get("tags", {}))
    return {k.upper(): v for k, v in tags.items()}


def decode_chunks(tags, prefix, count, encoding, expect_sha256=None):
    """Concatenate PREFIX_000..N-1, then undo the declared encoding."""
    if encoding not in SUPPORTED_ENCODINGS:
        raise SystemExit(f"unsupported payload encoding: {encoding!r}")

    parts = []
    for i in range(count):
        key = f"{prefix}{i:03d}"
        if key not in tags:
            raise SystemExit(f"missing payload chunk {key}")
        parts.append(tags[key])
    b64 = "".join(parts)

    # base64url, unpadded in the tags
    raw = base64.urlsafe_b64decode(b64 + "=" * (-len(b64) % 4))
    body = gzip.decompress(raw)

    if expect_sha256:
        got = hashlib.sha256(body).hexdigest()
        if got != expect_sha256.lower():
            raise SystemExit(
                f"payload sha256 mismatch: declared {expect_sha256}, got {got}"
            )
    return json.loads(body.decode("utf-8"))


def load_manifest(tags):
    fmt = tags.get("CASSINI_FORMAT")
    if not fmt:
        raise SystemExit("not a Cassini portable meeting: no CASSINI_FORMAT tag")
    count = int(tags.get("CASSINI_PAYLOAD_CHUNK_COUNT", "0"))
    if count <= 0:
        raise SystemExit("CASSINI_PAYLOAD_CHUNK_COUNT missing or zero")
    return decode_chunks(
        tags,
        prefix="CASSINI_PAYLOAD_",
        count=count,
        encoding=tags.get("CASSINI_PAYLOAD_ENCODING", ""),
        expect_sha256=tags.get("CASSINI_PAYLOAD_SHA256"),
    )


def transcript_entries(manifest):
    """v2/v3 transcripts plus readable transcripts; v1 is adapted to the same shape."""
    if manifest.get("version", 1) >= 2:
        return list(manifest.get("transcripts", [])) + list(
            manifest.get("readableTranscripts", [])
        )
    entries = []
    for key, role in (("transcript", "raw-asr"),
                      ("readableTranscript", "readable-cleanup"),
                      ("displayTranscript", "display")):
        body = manifest.get(key)
        if not body:
            continue
        entries.append({"id": key, "role": role, "inline": True,
                        "wordCount": body.get("wordCount")})
    return entries


def load_transcript(tags, manifest, wanted):
    for entry in transcript_entries(manifest):
        if entry.get("id") != wanted:
            continue
        if entry.get("inline"):
            # v1 keeps the body inside the manifest itself
            # v1 keeps the body under its own top-level key
            return manifest[wanted]
        ref = entry.get("payloadRef") or {}
        return decode_chunks(
            tags,
            prefix=ref["prefix"],
            count=int(ref["chunkCount"]),
            encoding=ref.get("encoding", ""),
            expect_sha256=ref.get("sha256"),
        )
    ids = ", ".join(e.get("id", "?") for e in transcript_entries(manifest))
    raise SystemExit(f"no transcript {wanted!r} in this file (have: {ids})")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--tags", action="store_true",
                    help="print the Cassini descriptor tags instead of the manifest")
    ap.add_argument("--list", action="store_true",
                    help="list the transcript ids this file carries")
    ap.add_argument("--transcript", metavar="ID",
                    help="print the named transcript body")
    args = ap.parse_args()

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

    if args.list:
        for entry in transcript_entries(manifest):
            flags = " (default)" if entry.get("default") else ""
            words = entry.get("wordCount")
            words = f"{words} words" if words is not None else "? words"
            print(f"{entry.get('id')}\t{entry.get('role', '?')}\t{words}{flags}")
        return

    if args.transcript:
        body = load_transcript(tags, manifest, args.transcript)
    else:
        body = manifest

    json.dump(body, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        # someone closed the pipe, e.g. `| head`
        sys.stderr.close()
        sys.exit(0)
