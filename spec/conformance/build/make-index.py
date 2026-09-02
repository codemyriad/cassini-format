"""Refresh index.json: recompute each vector's byte count and SHA-256 from the
file on disk, and stamp the date. Everything else in index.json is curated by
hand and is the source of truth; this script never rewrites it.

Run from spec/conformance/ after regenerating any vector.
SPDX-License-Identifier: CC0-1.0"""
import datetime, hashlib, json, pathlib

INDEX = pathlib.Path("index.json")
doc = json.loads(INDEX.read_text())
changed = 0
for v in doc["vectors"]:
    p = pathlib.Path(v["file"])
    if not p.exists():
        raise SystemExit(f"{v['id']}: {p} is missing")
    size, digest = p.stat().st_size, hashlib.sha256(p.read_bytes()).hexdigest()
    if (v.get("bytes"), v.get("sha256")) != (size, digest):
        v["bytes"], v["sha256"] = size, digest
        changed += 1
if changed:
    doc["updated"] = datetime.date.today().isoformat()
INDEX.write_text(json.dumps(doc, indent=2) + "\n")
print(f"index.json: {len(doc['vectors'])} vectors, {changed} refreshed")
