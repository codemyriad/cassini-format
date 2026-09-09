#!/usr/bin/env python3
"""Prepare separate speaker tracks from the reviewed ElevenLabs dialogue takes.

    python3 site/scripts/produce-demo.py --cache /path/to/reviewed-stems --out DIR

Requires numpy and ffmpeg. Makes no API calls and writes no Cassini transcript.
Feed the resulting multitrack recording to Cassini itself for processing.
Scribe timings here are used only for edits and the independent QA reference.
SPDX-License-Identifier: CC0-1.0
"""
import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import wave

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
DEMO = ROOT / "site/static/demo"
RATE = 24000


def read_json(path):
    return json.loads(path.read_text())


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def pcm(path):
    with wave.open(str(path), "rb") as wav:
        assert (wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) == (1, 2, RATE)
        return np.frombuffer(wav.readframes(wav.getnframes()), dtype="<i2").astype(np.float64) / 32768


def wav(path, samples):
    with wave.open(str(path), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(RATE)
        out.writeframes(np.round(samples * 32767).astype("<i2").tobytes())


def ffmpeg(args):
    common = ["ffmpeg", "-y", "-v", "error"]
    accel = ["-hwaccel", "vaapi", "-hwaccel_device", "/dev/dri/renderD128", "-hwaccel_output_format", "vaapi"]
    if pathlib.Path("/dev/dri/renderD128").exists():
        result = subprocess.run(common + accel + args, capture_output=True)
        if result.returncode == 0:
            return
    subprocess.run(common + args, check=True)


def normalized(text):
    return re.sub(r"[^a-z0-9:]", "", text.lower())


def tighten_scene(samples, turns):
    """Edit only silence between turns; preserve every within-turn hesitation."""
    cuts = []
    # Retain the complete opening: ASR can miss the unvoiced onset of "So".
    for index, (before, after) in enumerate(zip(turns, turns[1:])):
        end = before["words"][-1]["end"]
        start = after["words"][0]["start"]
        # Deliberately small variation, no unnaturally uniform metronome.
        gap = [.32, .38, .28, .34][index % 4]
        if start - end > gap + .1:
            cuts.append((round((end + gap / 2) * RATE), round((start - gap / 2) * RATE)))
    end = turns[-1]["words"][-1]["end"]
    if len(samples) / RATE - end > .2:
        cuts.append((round((end + .2) * RATE), len(samples)))
    parts, previous = [], 0
    for start, end in cuts:
        segment = samples[previous:start].copy()
        # The joins sit in silence; a 5 ms fade prevents codec/noise-floor clicks.
        fade = min(120, len(segment) // 2)
        if fade:
            segment[:fade] *= np.linspace(0, 1, fade)
            segment[-fade:] *= np.linspace(1, 0, fade)
        parts.append(segment)
        previous = end
    parts.append(samples[previous:])
    for turn in turns:
        for word in turn["words"]:
            for field in ("start", "end"):
                position = word[field] * RATE
                assert not any(a < position < b for a, b in cuts), "Edit crosses speech"
                word[field] -= sum(b - a for a, b in cuts if b <= position) / RATE
    return np.concatenate(parts), [{"startSample": a, "endSample": b} for a, b in cuts]


def main(cache, output):
    output.mkdir(parents=True, exist_ok=True)
    script_path = DEMO / "repair-cafe.script.json"
    script = read_json(script_path)
    tracks, items, placements, scene_records = [], [], [], []
    speaker_parts = {speaker["id"]: [] for speaker in script["speakers"]}
    offset_samples = 0
    for scene in script["scenes"]:
        name = scene["id"]
        samples = pcm(cache / f"{name}.wav")
        aligned = read_json(cache / f"{name}.aligned.json")
        samples, silence_cuts = tighten_scene(samples, aligned["turns"])
        offset = offset_samples / RATE
        scene_records.append({"id": name, "startMs": round(offset * 1000), "samples": len(samples), "silenceCuts": silence_cuts,
                              "wavSha256": hashlib.sha256((cache / f"{name}.wav").read_bytes()).hexdigest()})
        # Split the already generated dialogue in quiet gaps, before mixing
        # acknowledgments. This preserves cross-turn prosody and gives each
        # participant an isolated track, without audio source separation.
        boundaries = [0]
        for before, after in zip(aligned["turns"], aligned["turns"][1:]):
            boundary = round((before["words"][-1]["end"] + after["words"][0]["start"]) * RATE / 2)
            neighborhood = samples[max(0, boundary - 120):boundary + 120]
            rms = float(np.sqrt(np.mean(neighborhood ** 2)))
            assert rms < 10 ** (-45 / 20), f"Speaker boundary is not quiet: {name} at {boundary / RATE}s"
            boundaries.append(boundary)
        boundaries.append(len(samples))
        scene_tracks = {speaker: np.zeros_like(samples) for speaker in speaker_parts}
        for index, (authored, turn) in enumerate(zip(scene["turns"], aligned["turns"], strict=True)):
            scene_tracks[authored["speaker"]][boundaries[index]:boundaries[index + 1]] = samples[boundaries[index]:boundaries[index + 1]]
            assert authored["id"] == turn["id"]
            words = turn["words"]
            for word in words:
                assert 0 <= word["start"] < word["end"] <= len(samples) / RATE + .002
                items.append({"speaker": authored["speaker"], "text": word["text"],
                              "startMs": round((offset + word["start"]) * 1000),
                              "endMs": round((offset + min(word["end"], len(samples) / RATE)) * 1000)})
            for aside in authored.get("interjections", []):
                source = pcm(cache / f'{aside["id"]}.wav')
                utterance = read_json(cache / f'{aside["id"]}.aligned.json')["turns"][1]["words"]
                # ASR boundaries can miss unvoiced consonants. Keep 150 ms
                # handles, checked to be clear of the surrounding context.
                start = max(0, round((utterance[0]["start"] - .15) * RATE))
                end = min(len(source), round((utterance[-1]["end"] + .15) * RATE))
                clip = source[start:end].copy()
                # Short fades remove splice clicks without moving the speech.
                fade = min(240, len(clip) // 2)
                clip[:fade] *= np.linspace(0, 1, fade)
                clip[-fade:] *= np.linspace(1, 0, fade)
                anchor = aside["afterWordOrPhrase"].replace("eleven fifteen", "11:15").split()
                needle = list(map(normalized, anchor))
                haystack = [normalized(w["text"]) for w in words]
                matches = [i for i in range(len(words) - len(needle)) if haystack[i:i + len(needle)] == needle]
                assert len(matches) == 1, f"Ambiguous interjection anchor: {aside}"
                last = matches[0] + len(needle) - 1
                # Land just inside the continuing phrase, including a natural
                # breath after the anchor rather than speaking into that breath.
                onset = max(words[last]["end"] + .06, words[last + 1]["start"] + .04)
                destination = round((onset - (utterance[0]["start"] - start / RATE)) * RATE)
                assert destination >= 0 and destination + len(clip) <= len(samples)
                gain = .72
                samples[destination:destination + len(clip)] += clip * gain
                scene_tracks[aside["speaker"]][destination:destination + len(clip)] += clip * gain
                word_shift = offset + (destination - start) / RATE
                for word in utterance:
                    items.append({"speaker": aside["speaker"], "text": word["text"],
                                  "startMs": round((word_shift + word["start"]) * 1000),
                                  "endMs": round((word_shift + word["end"]) * 1000)})
                placements.append({"id": aside["id"], "speaker": aside["speaker"], "hostTurn": authored["id"],
                                   "text": " ".join(w["text"] for w in utterance),
                                   "startMs": round((offset + onset) * 1000),
                                   "endMs": round((word_shift + utterance[-1]["end"]) * 1000),
                                   "sourceStartSample": start, "sourceEndSample": end,
                                   "destinationSample": offset_samples + destination, "gain": gain})
        # With separated tracks, their sum must reconstruct the authored mix.
        assert np.allclose(sum(scene_tracks.values()), samples, atol=1e-14, rtol=0)
        for speaker, samples_for_speaker in scene_tracks.items():
            speaker_parts[speaker].append(samples_for_speaker)
        tracks.append(samples)
        offset_samples += len(samples)
    mix = np.concatenate(tracks)
    peak = float(np.max(np.abs(mix)))
    master_gain = min(1, .89 / peak)
    mix *= master_gain
    items.sort(key=lambda w: w["startMs"])
    speakers = [{"id": s["id"], "label": s["label"]} for s in script["speakers"]]
    fixture = {"synthetic": True, "script": "repair-cafe.script.json",
               "scriptSha256": hashlib.sha256(script_path.read_bytes()).hexdigest(),
               "synthesis": {"provider": "ElevenLabs", "model": "eleven_v3",
                             "voices": {s["id"]: s["voiceId"] for s in script["speakers"]}},
               "editTimingReference": "Scribe v2 word boundaries, verified against the script; used only to schedule source edits",
               "mix": "Continuous dialogue scenes with separately generated acknowledgments mixed over speech",
               "interjections": placements}
    record = {"title": script["title"], "createdAtUtc": script["production"]["createdAtUtc"],
              "sampleRate": RATE, "scenes": scene_records, "masterGain": master_gain,
              "fixture": fixture, "requests": {name: read_json(cache / f"{name}.request.json")
                  for name in [s["id"] for s in script["scenes"]] + [p["id"] for p in placements]}}
    record["transcriptNote"] = "Scribe timing is an editing/QA reference only. Cassini must recognize and align the multitrack audio independently."
    record["tracks"] = []
    for speaker in script["speakers"]:
        audio = np.concatenate(speaker_parts[speaker["id"]]) * master_gain
        destination = output / f'{speaker["id"]}.wav'
        wav(destination, audio)
        record["tracks"].append({"speaker": speaker["id"], "label": speaker["label"],
                                  "file": destination.name, "sampleRate": RATE, "sampleCount": len(audio),
                                  "sha256": hashlib.sha256(destination.read_bytes()).hexdigest()})
    wav(output / "mix-reference.wav", mix)
    write_json(output / "reference.words.json", {"speakers": speakers, "items": items})
    # The input container is lossless. Cassini will make the public Opus mix.
    inputs = [arg for speaker in script["speakers"] for arg in ["-i", str(output / f'{speaker["id"]}.wav')]]
    options = []
    for index, speaker in enumerate(script["speakers"]):
        options += ["-map", f"{index}:a:0", f"-metadata:s:a:{index}", f'title={speaker["label"]}',
                    f"-metadata:s:a:{index}", f'participant_id={speaker["id"]}',
                    f"-metadata:s:a:{index}", f'participant_name={speaker["label"]}',
                    f"-metadata:s:a:{index}", "language=eng"]
    multitrack = output / "repair-cafe.multitrack.mkv"
    ffmpeg(inputs + options + ["-c:a", "flac", "-metadata", f'title={script["title"]}',
                              "-metadata", "comment=Fictional volunteers; Eleven v3 synthetic voices; separate participant tracks.", str(multitrack)])
    record["multitrack"] = {"file": multitrack.name, "bytes": multitrack.stat().st_size,
                              "sha256": hashlib.sha256(multitrack.read_bytes()).hexdigest()}
    write_json(output / "source-production.json", record)
    print(json.dumps({"tracks": record["tracks"], "multitrack": record["multitrack"]}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    args = parser.parse_args()
    main(args.cache, args.out)
