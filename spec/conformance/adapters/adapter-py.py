#!/usr/bin/env python3
"""Conformance adapter for tools/cassini-extract.py.

The whole contract: take a path, print ONE observation object on stdout, exit 0.
Everything an implementer has to write to run this suite against their reader.
SPDX-License-Identifier: CC0-1.0"""
import importlib.util, json, pathlib, sys

_s = importlib.util.spec_from_file_location(
    "cx", str(pathlib.Path(__file__).resolve().parents[3] / "tools" / "cassini-extract.py"))
cx = importlib.util.module_from_spec(_s); _s.loader.exec_module(cx)


def code_for(msg):
    """Map the reader's prose onto the suite's error vocabulary."""
    return ("payload-sha256-mismatch" if "sha256 mismatch" in msg else
            "chunk-missing" if "missing payload chunk" in msg else
            "base64-invalid" if "base64url decode failed" in msg else
            "payload-bytes-mismatch" if "byte count mismatch" in msg else
            "decode-failed")

obs = {"reader": "tools/cassini-extract.py", "profile": "metadata"}
try:
    tags = cx.read_tags(sys.argv[1])
    try:
        manifest = cx.load_manifest(tags)
    except cx.PlainAudio:
        obs.update(state="plain-audio", classification="plain-audio", payloadTrust="not-applicable",
                   audioTrust="not-applicable", errors=[], warnings=[])
        print(json.dumps(obs)); raise SystemExit
    fmt = tags.get("CASSINI_FORMAT", "")
    obs.update(state="unverified", classification="cassini", payloadTrust="verified",
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
        # A body that fails its checks is unavailable; the file's state is unchanged.
        try:
            body = cx.load_transcript(tags, manifest, e["id"])
        except cx.DuplicateTag:
            raise                                  # a repeat is file-level
        except cx.CassiniError as exc:
            obs["errors"].append({"code": code_for(str(exc)),
                                  "message": f"transcript {e['id']!r} is unavailable: {exc}"})
            continue
        counts[e["id"]] = len(body.get("items") or [])
        bodies[e["id"]] = body
    obs["wordCounts"] = counts
    obs["_manifest"], obs["_transcripts"] = manifest, bodies
except cx.UnknownFormat as exc:
    # A major version this reader does not implement: play the audio, say so,
    # present nothing.
    obs.update(state="unknown-cassini-format", classification="unsupported-version",
               formatId=tags.get("CASSINI_FORMAT"),
               payloadTrust="unverified", audioTrust="not-checked",
               errors=[], warnings=[{"code": "unsupported-version", "message": str(exc)}])
except cx.CassiniError as exc:
    # Map the reader's prose onto the suite's error vocabulary. Every adapter
    # has to do this; a reader that emitted the codes itself would not.
    msg = str(exc)
    code = code_for(msg)
    trust = "mismatched" if code == "payload-sha256-mismatch" else "unverified"
    obs.update(state="invalid-cassini-metadata", classification="damaged-metadata", payloadTrust=trust,
               audioTrust="not-checked",
               errors=[{"code": code, "message": msg}], warnings=[])
except Exception as exc:                      # a crash is an observation too
    obs.update(state="crash", classification="crash", errors=[{"code": "crash",
                                                "message": f"{type(exc).__name__}: {exc}"}])
print(json.dumps(obs))
