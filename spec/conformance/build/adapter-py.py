#!/usr/bin/env python3
"""Conformance adapter for tools/cassini-extract.py.

The whole contract: take a path, print ONE observation object on stdout, exit 0.
Everything an implementer has to write to run this suite against their reader.
SPDX-License-Identifier: CC0-1.0"""
import importlib.util, json, pathlib, sys

_s = importlib.util.spec_from_file_location(
    "cx", "/home/silvio/dev/cassini-format/tools/cassini-extract.py")
cx = importlib.util.module_from_spec(_s); _s.loader.exec_module(cx)

obs = {"reader": "tools/cassini-extract.py", "profile": "metadata"}
try:
    tags = cx.read_tags(sys.argv[1])
    try:
        manifest = cx.load_manifest(tags)
    except cx.PlainAudio:
        obs.update(classification="plain-audio", payloadTrust="not-applicable",
                   audioTrust="not-applicable", errors=[], warnings=[])
        print(json.dumps(obs)); raise SystemExit
    fmt = tags.get("CASSINI_FORMAT", "")
    obs.update(classification="cassini", payloadTrust="verified",
               audioTrust="not-checked", formatId=fmt,
               manifestVersion=manifest.get("version"),
               manifestKind=manifest.get("kind"),
               speakerIds=[s.get("id") for s in manifest.get("speakers", [])],
               errors=[], warnings=[])
    if fmt.lower() not in cx.KNOWN_FORMATS:
        obs["warnings"].append({"code": "unsupported-version"})
    entries = cx.transcript_entries(manifest)
    obs["transcriptIds"] = [e.get("id") for e in entries]
    obs["defaultTranscriptId"] = cx.default_transcript_id(tags, manifest)
    counts, bodies = {}, {}
    for e in entries:
        body = cx.load_transcript(tags, manifest, e["id"])
        counts[e["id"]] = len(body.get("items") or [])
        bodies[e["id"]] = body
    obs["wordCounts"] = counts
    obs["_manifest"], obs["_transcripts"] = manifest, bodies
except cx.CassiniError as exc:
    # Map the reader's prose onto the suite's error vocabulary. Every adapter
    # has to do this; a reader that emitted the codes itself would not.
    msg = str(exc)
    code = ("payload-sha256-mismatch" if "sha256 mismatch" in msg else
            "chunk-missing" if "missing payload chunk" in msg else
            "base64-invalid" if "base64url decode failed" in msg else
            "payload-bytes-mismatch" if "byte count mismatch" in msg else
            "decode-failed")
    trust = "mismatched" if code == "payload-sha256-mismatch" else "unverified"
    obs.update(classification="damaged-metadata", payloadTrust=trust,
               audioTrust="not-checked",
               errors=[{"code": code, "message": msg}], warnings=[])
except Exception as exc:                      # a crash is an observation too
    obs.update(classification="crash", errors=[{"code": "crash",
                                                "message": f"{type(exc).__name__}: {exc}"}])
print(json.dumps(obs))
