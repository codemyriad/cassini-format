#!/usr/bin/env python3
"""Copy reviewed Cassini-produced fixtures into the site without rewriting them.

The transcript JSON and production record are exported from the exact files
visitors download. This script does not synthesize, transcribe, align or retag.
SPDX-License-Identifier: CC0-1.0
"""
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

DEMO = Path(__file__).resolve().parents[1] / "static/demo"


def read_json(path):
    return json.loads(path.read_text())


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(path):
    probe = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "stream_tags", "-of", "json", str(path)
    ]))
    tags = probe["streams"][0]["tags"]

    def decode(prefix):
        text = "".join(tags[f"{prefix}{i:03d}"] for i in range(int(tags[prefix + "CHUNK_COUNT"])))
        raw = gzip.decompress(base64.urlsafe_b64decode(text + "=" * (-len(text) % 4)))
        assert hashlib.sha256(raw).hexdigest() == tags[prefix + "SHA256"], "Payload digest mismatch"
        return json.loads(raw)

    manifest = decode("CASSINI_PAYLOAD_")
    entry = next(t for t in manifest["transcripts"] if t["id"] == tags["CASSINI_TRANSCRIPT_DEFAULT"])
    transcript = decode(entry["payloadRef"]["prefix"])
    assert transcript["wordCount"] == len(transcript["items"])
    assert manifest["provenance"]["speechToText"][entry["id"]]["backend"] == "sherpa-onnx"
    assert manifest["provenance"]["wordTimings"]["endsBoundedByAudio"] is True
    return manifest, entry, transcript


def main(args):
    source = read_json(args.source_record)
    processor = read_json(args.processor_record)
    # Validate everything before replacing either public fixture.
    decoded = [(path, name, inspect(path)) for path, name in (
        (args.full, "repair-cafe"), (args.excerpt, "repair-cafe-excerpt")
    )]
    outputs = []
    for path, name, (manifest, entry, transcript) in decoded:
        target = DEMO / f"{name}.opus"
        shutil.copyfile(path, target)
        assert sha256(target) == sha256(path), "Published bytes differ from Cassini output"
        write_json(DEMO / f"{name}.words.json", {"speakers": manifest["speakers"], "items": transcript["items"]})
        outputs.append({"file": target.name, "bytes": target.stat().st_size,
                        "durationMs": manifest["audio"]["durationMs"],
                        "speakers": len(manifest["speakers"]), "words": len(transcript["items"]),
                        "transcriptId": entry["id"], "sha256": sha256(target),
                        "opusAudioSha256": manifest["integrity"]["opusAudioSha256"],
                        "provenance": manifest["provenance"]})
    multitrack = DEMO / "repair-cafe.multitrack.mkv"
    shutil.copyfile(args.tracks, multitrack)
    record = {"title": source["title"], "synthetic": True,
              "sourceProduction": source, "cassiniProcessing": processor,
              "multitrack": {"file": multitrack.name, "bytes": multitrack.stat().st_size,
                             "sha256": sha256(multitrack)}, "outputs": outputs,
              "transcriptSource": "Unedited Cassini recognition from separate participant audio tracks. No scripted words or external timestamps were supplied to Cassini."}
    write_json(DEMO / "repair-cafe.production.json", record)
    print(json.dumps(outputs, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("full", "excerpt", "tracks", "source-record", "processor-record"):
        parser.add_argument("--" + name, type=Path, required=True)
    main(parser.parse_args())
