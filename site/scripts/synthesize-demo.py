#!/usr/bin/env python3
"""Generate/cache the demo's Eleven v3 dialogue and independent Scribe recognition.

    ELEVENLABS_API_KEY=... python3 site/scripts/synthesize-demo.py --cache DIR --generate

Requires requests. --generate explicitly enables billable API calls for missing
stems; existing matching requests are reused. Never called by the site build.
SPDX-License-Identifier: CC0-1.0
"""
import argparse
import base64
import json
import os
from pathlib import Path
import wave

import requests

SCRIPT = Path(__file__).resolve().parents[1] / "static/demo/repair-cafe.script.json"
API = "https://api.elevenlabs.io/v1"


def requests_for(script):
    production = script["production"]
    voices = {s["id"]: s["voiceId"] for s in script["speakers"]}
    common = {"model_id": production["model"], "language_code": "en",
              "settings": {"stability": production["stability"]}, "apply_text_normalization": "off"}
    for index, scene in enumerate(script["scenes"]):
        inputs = [{"text": t["text"], "voice_id": voices[t["speaker"]]} for t in scene["turns"]]
        yield scene["id"], dict(common, inputs=inputs, seed=production["seed"] + index)
    for scene in script["scenes"]:
        for turn in scene["turns"]:
            for aside in turn.get("interjections", []):
                # Context gives a short acknowledgment a conversational reading.
                # Only its own isolated acoustic interval enters the final mix.
                text = turn["text"]
                split = text.index(aside["afterWordOrPhrase"]) + len(aside["afterWordOrPhrase"])
                inputs = [
                    {"text": text[:split].rstrip(",.") + ".", "voice_id": voices[turn["speaker"]]},
                    {"text": aside["text"], "voice_id": voices[aside["speaker"]]},
                    {"text": text[split:].lstrip(", ."), "voice_id": voices[turn["speaker"]]}
                ]
                yield aside["id"], dict(common, inputs=inputs, seed=production["seed"] + int(aside["id"][1:]) + 100)


def main(cache, generate):
    script = json.loads(SCRIPT.read_text())
    cache.mkdir(parents=True, exist_ok=True)

    def post(endpoint, **kwargs):
        if not generate:
            raise SystemExit("Cache incomplete. Use --generate to enable ElevenLabs API calls.")
        key = os.environ.get("ELEVENLABS_API_KEY")
        if not key:
            raise SystemExit("ELEVENLABS_API_KEY is required for generation.")
        response = requests.post(f"{API}/{endpoint}", headers={"xi-api-key": key}, timeout=240, **kwargs)
        if not response.ok:
            raise SystemExit(f"ElevenLabs returned HTTP {response.status_code}: {response.text[:600]}")
        return response.json()

    for name, request in requests_for(script):
        request_path = cache / f"{name}.request.json"
        response_path = cache / f"{name}.json"
        if request_path.exists() and json.loads(request_path.read_text()) != request:
            raise SystemExit(f"{name}: cached request differs. Use a fresh cache directory for the revised script.")
        if not response_path.exists():
            print(f"Generating {name}…", flush=True)
            result = post(f'text-to-dialogue/with-timestamps?output_format={script["production"]["outputFormat"]}', json=request)
            request_path.write_text(json.dumps(request, indent=2) + "\n")
            response_path.write_text(json.dumps(result) + "\n")
        elif not request_path.exists():
            raise SystemExit(f"{name}: cached audio has no corresponding request; refusing uncertain provenance.")
        result = json.loads(response_path.read_text())
        audio_path = cache / f"{name}.wav"
        with wave.open(str(audio_path), "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(script["production"]["sampleRate"])
            audio.writeframes(base64.b64decode(result["audio_base64"]))
        recognized = cache / f"{name}.scribe.json"
        if not recognized.exists():
            print(f"Independently recognizing {name}…", flush=True)
            with audio_path.open("rb") as source:
                transcript = post("speech-to-text", files={"file": (audio_path.name, source, "audio/wav")},
                                  data={"model_id": "scribe_v2", "language_code": "en", "tag_audio_events": "false",
                                        "diarize": "true", "num_speakers": "3"})
            recognized.write_text(json.dumps(transcript, indent=2) + "\n")
        print(f"Cached {name}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--generate", action="store_true")
    args = parser.parse_args()
    main(args.cache, args.generate)
