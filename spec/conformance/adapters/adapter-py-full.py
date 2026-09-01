#!/usr/bin/env python3
"""Full-profile adapter: tools/cassini-extract.py for the metadata,
tools/cassini-opus-digest.py for the audio. Neither tool does both, and the
suite's 'full' profile is what makes that visible.
SPDX-License-Identifier: CC0-1.0"""
import importlib.util, json, pathlib, subprocess, sys

def load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

# Resolve the repo's tools relative to this file, so the suite runs anywhere.
T = str(pathlib.Path(__file__).resolve().parents[3] / "tools") + "/"
base = subprocess.run([sys.executable, str(pathlib.Path(__file__).with_name("adapter-py.py")), sys.argv[1]],
                      capture_output=True, text=True)
obs = json.loads(base.stdout)
obs["reader"] = "cassini-extract.py + cassini-opus-digest.py"
obs["profile"] = "full"
dig = load("dig", T + "cassini-opus-digest.py")
try:
    a = dig.compute(sys.argv[1])
except Exception as exc:
    obs["audioTrust"] = "unverified"
    obs.setdefault("warnings", []).append({"code": "audio-unreadable", "message": str(exc)})
    print(json.dumps(obs)); raise SystemExit
obs["audioOpusSha256"] = a["sha256"]
m = obs.get("_manifest") or {}
integ, tags = m.get("integrity") or {}, None
if obs.get("classification") == "plain-audio":
    obs["audioTrust"] = "not-applicable"
else:
    # The tag and the manifest must agree before either can be checked.
    tagged = load("cx", T + "cassini-extract.py").read_tags(sys.argv[1]).get(
        "CASSINI_AUDIO_OPUS_SHA256", "")
    claimed = integ.get("opusAudioSha256", "")
    if tagged and claimed and tagged.lower() != claimed.lower():
        obs["audioTrust"] = "unverified"
        obs.setdefault("warnings", []).append(
            {"code": "tag-manifest-disagreement", "tag": "CASSINI_AUDIO_OPUS_SHA256"})
    elif not claimed:
        obs["audioTrust"] = "unverified"
    elif claimed.lower() == a["sha256"]:
        obs["audioTrust"] = "verified"
    else:
        obs["audioTrust"] = "mismatched"
        obs.setdefault("warnings", []).append({"code": "audio-digest-mismatch"})
        if integ.get("sampleCount") != a["sampleCount"]:
            obs["warnings"].append({"code": "audio-shape-mismatch"})
obs.pop("_manifest", None); obs.pop("_transcripts", None)

# This reader does check the audio, so the state follows the audio verdict.
if obs.get("classification") == "cassini":
    obs["state"] = {"verified": "ok", "mismatched": "stale-audio"}.get(
        obs.get("audioTrust"), "unverified")

print(json.dumps(obs))
