#!/usr/bin/env python3
"""Conformance adapter for the reference Go reader, `cassini inspect`.

It has no machine-readable mode, so this parses its key=value lines. Anything
this adapter cannot see, the reader did not say.
SPDX-License-Identifier: CC0-1.0"""
import json, os, re, subprocess, sys

BIN = os.environ.get("CASSINI_BIN", "cassini")
# `cassini inspect` prints a speaker COUNT, not ids, and never prints the
# manifest's kind or version. A reader is not non-conforming for not printing
# something; it is only non-conforming for getting something wrong.
obs = {"reader": "cassini inspect", "profile": "full", "errors": [], "warnings": [],
       "omits": ["manifestVersion", "manifestKind", "speakerIds"]}
p = subprocess.run([BIN, "inspect", sys.argv[1]], capture_output=True, text=True)
text = p.stdout + p.stderr
kv = dict(re.findall(r"(\w+)=(\S+)", text.splitlines()[0] if text.strip() else ""))
status = kv.get("cassini", "")

obs["classification"] = {
    "ok": "cassini", "plain-audio": "plain-audio", "stale-audio": "cassini",
    "integrity-unverified": "cassini", "invalid-cassini-metadata": "damaged-metadata",
    "unknown-cassini-format": "unsupported-version",
}.get(status, "crash")
obs["payloadTrust"] = {"invalid-cassini-metadata": "unverified",
                       "unknown-cassini-format": "unverified"}.get(status, "verified")
obs["audioTrust"] = {"ok": "verified", "stale-audio": "mismatched",
                     "integrity-unverified": "unverified",
                     "plain-audio": "not-applicable"}.get(status, "unverified")
if status == "plain-audio":
    obs["payloadTrust"] = "not-applicable"
for w in re.findall(r"warning=([^\n]*)", text):
    code = ("audio-digest-mismatch" if "sha256 mismatch:" in w else
            "tag-manifest-disagreement" if "between manifest and tag" in w else
            "audio-shape-mismatch" if ("sample count mismatch" in w or "duration mismatch" in w) else
            "payload-sha256-mismatch" if "payload sha256 mismatch" in w else
            "base64-invalid" if "illegal base64" in w else
            "unsupported-version" if "unsupported CASSINI_FORMAT" in w else "reader-warning")
    (obs["errors"] if obs["classification"] == "damaged-metadata"
     else obs["warnings"]).append({"code": code, "message": w.strip()})
if obs["classification"] == "damaged-metadata" and not obs["errors"]:
    obs["errors"].append({"code": "decode-failed"})
if status == "invalid-cassini-metadata" and any(
        e["code"] == "payload-sha256-mismatch" for e in obs["errors"]):
    obs["payloadTrust"] = "mismatched"

if "opus_sha256=" in text:
    obs["audioOpusSha256"] = re.search(r"opus_sha256=(\w+)", text).group(1)
if obs["classification"] == "plain-audio":
    obs["omits"].append("audioOpusSha256")
if obs["classification"] == "unsupported-version":
    obs["formatId"] = re.search(r"CASSINI_FORMAT=(\S+)", text).group(1)
if obs["classification"] == "cassini":
    obs["formatId"] = "org.cassini.portable-meeting/" + (
        re.search(r"manifest-v(\d+)\.schema", text).group(1) if "schema=" in text else "?")
    obs["totalWordCount"] = int(kv["words"]) if "words" in kv else None
    ids, counts, default = [], {}, None
    for line in text.splitlines():
        if not line.startswith("transcript id="):
            continue
        d = dict(re.findall(r"(\w+)=(\S+)", line))
        ids.append(d["id"])
        counts[d["id"]] = int(d["word_count"])
        if d.get("default") == "yes":
            default = d["id"]
    obs["transcriptIds"], obs["defaultTranscriptId"] = ids, default
    # cassini inspect reports the DECLARED word count without decoding a body,
    # so re-run the one command that does decode and let it contradict us.
    t = subprocess.run([BIN, "inspect", "--transcript", sys.argv[1]],
                       capture_output=True, text=True)
    if "failed:" in (t.stdout + t.stderr):
        msg = (t.stdout + t.stderr).strip()
        obs["classification"] = "damaged-metadata"
        obs["payloadTrust"] = "unverified"
        obs["errors"].append({
            "code": ("chunk-missing" if "missing transcript chunk" in msg else
                     "base64-invalid" if "illegal base64" in msg else "decode-failed"),
            "message": msg})
        obs["wordCounts"] = {}
    else:
        obs["wordCounts"] = counts
print(json.dumps(obs))
