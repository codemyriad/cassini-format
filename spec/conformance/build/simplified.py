"""Build origin-label regression vectors without changing the legacy corpus.

Run from any directory. The source files are checked-in synthetic vectors;
only OpusTags change, with audio packets copied verbatim.
SPDX-License-Identifier: CC0-1.0
"""
import base64
import copy
import gzip
import json
from pathlib import Path
import subprocess
import sys

from opustags import pack, read_comments, write_comments

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "opus"
ROOT = HERE.parents[2]
PREFIX = "CASSINI_PAYLOAD_"
MIME = "application/vnd.cassini.portable-meeting+json"


def manifest(comments):
    tags = dict(comments)
    joined = "".join(tags[f"{PREFIX}{i:03d}"]
                     for i in range(int(tags[PREFIX + "CHUNK_COUNT"])))
    return json.loads(gzip.decompress(base64.urlsafe_b64decode(
        joined + "=" * (-len(joined) % 4))))


def rewrite(name, comments, doc, default_id):
    raw, gz, chunks, sha = pack.encode_payload(doc)
    kept = [(k, v) for k, v in comments
            if not k.startswith(PREFIX) or k == PREFIX + "SCHEMA"]
    kept = [(k, default_id if k == "CASSINI_TRANSCRIPT_DEFAULT" else v)
            for k, v in kept]
    write_comments(OUT / "016-two-transcripts.opus", OUT / name,
                   sorted(kept + pack.chunk_tags(PREFIX, MIME, raw, gz, chunks, sha)))


def main():
    subprocess.run([
        sys.executable, str(ROOT / "tools/cassini-pack.py"),
        str(OUT / "001-minimal-v1.opus"), str(HERE / "tiny-transcript.json"),
        str(OUT / "023-no-transcript-role.opus"),
        "--title", "Transcript without an origin label",
        "--created-at", "2026-09-07T00:00:00Z",
    ], check=True)

    _, comments = read_comments(OUT / "016-two-transcripts.opus")
    doc = manifest(comments)
    for i, entry in enumerate(doc["transcripts"]):
        entry.pop("role", None)
        entry["default"] = i == 1
    rewrite("024-no-role-second-default.opus", comments, doc, "second-pass")

    doc = copy.deepcopy(doc)
    for entry in doc["transcripts"]:
        entry.pop("default", None)
        entry["role"] = "unknown-origin"
        entry["sourceTranscriptId"] = "not-declared"
    # These fields were removed from the current contract and must be ignored
    # as unknown metadata, not make the file invalid.
    doc["meeting"].update(language="en", summary="Old summary hint", roomName="Old room")
    doc["chapters"] = [{"startMs": 0, "title": "Old chapter"}]
    rewrite("025-ignored-origin-label.opus", comments, doc, "raw-asr")

    doc = manifest(comments)
    for entry in doc["transcripts"]:
        entry.pop("role", None)
        entry.pop("sourceTranscriptId", None)
    display = {
        "version": "transcript.display.v1",
        "blocks": [{"id": "d1", "text": "One two. Three."}],
    }
    raw, gz, chunks, sha = pack.encode_payload(display)
    prefix = "CASSINI_TX_DISPLAY_PAYLOAD_"
    mime = "application/vnd.cassini.transcript-readable+json"
    doc["readableTranscripts"] = [
        # Deliberately unavailable: readers must skip its body and source link.
        {"id": "old-cleanup", "role": "readable-cleanup",
         "sourceTranscriptId": "missing", "format": "transcript.readable.v1",
         "payloadRef": {"prefix": "CASSINI_TX_CLEANUP_PAYLOAD_", "chunkCount": 1,
                        "sha256": "0" * 64, "rawBytes": 0, "gzipBytes": 0,
                        "mime": mime, "encoding": "base64url+gzip+utf8json"}},
        {"id": "display", "role": "display", "sourceTranscriptId": "raw-asr",
         "format": "transcript.display.v1",
         "payloadRef": {"prefix": prefix, "chunkCount": len(chunks),
                        "sha256": sha, "rawBytes": len(raw), "gzipBytes": len(gz),
                        "mime": mime, "encoding": "base64url+gzip+utf8json"}},
    ]
    rewrite("026-display-and-withdrawn-cleanup.opus",
            comments + pack.chunk_tags(prefix, mime, raw, gz, chunks, sha), doc, "raw-asr")


if __name__ == "__main__":
    main()
