A file can open successfully while some checks have not run. Decide what you
need to establish, then use the corresponding check:

| Question | What answers it | What it does not establish |
| --- | --- | --- |
| Can I read and listen? | [Open the file in the browser](/try/). It checks the manifest and selected transcript payload and reports any problems. | This browser reader does not check the audio match. |
| Is the embedded data intact? | Decode the payloads and compare their digests and byte counts, below. | That the words accurately describe the recording. |
| Does the audio match the stored claim? | Compute the audio digest and compare it with the metadata, below. | Authenticity, the identity of a speaker, or transcription accuracy. |
| Does my producer write the required structure? | Validate the JSON and review the cross-field requirements. | That a reader behaves correctly on other files. Use the [conformance suite](/build/#check-a-file-then-test-your-implementation) for that. |

“Unverified” means the audio match has not been established. It is different
from “stale audio,” where a check found a mismatch. You can still read recovered
text and listen; take care when relying on words that may describe different
audio. [How this affects a shared file](/using/#what-stays-with-the-file).

## Prepare a file and the tools

The command-line steps below use **Python 3, curl and ffprobe** (part of FFmpeg).
They work in a shell on Linux or macOS. The schema step adds one Python package.
Run the commands in the same directory so the downloaded modules can be imported.

Download the two CC0 tools:

```bash
curl -fLo cassini_extract.py https://raw.githubusercontent.com/codemyriad/cassini-format/main/tools/cassini-extract.py
curl -fLo cassini_digest.py https://raw.githubusercontent.com/codemyriad/cassini-format/main/tools/cassini-opus-digest.py
```

Choose the file you produced or received:

```bash
CASSINI_FILE=meeting.opus
```

Or, to practise with the site's example, download it and select it instead:

```bash
curl -fLo example.opus https://format.gocassini.com/demo/{{demo.filename}}
CASSINI_FILE=example.opus
```

## Check the embedded data

```bash
python3 cassini_extract.py "$CASSINI_FILE" --check
```

For a readable Cassini file this prints `ok` for the manifest and each decoded
transcript. A missing chunk, damaged payload or mismatched digest stops the
check with an explanation. This checks payload bytes, not every semantic rule
in the specification. ffprobe also merges duplicate comment names, so this tool
cannot detect every duplicate-tag error.

An ordinary audio file or an unsupported format is reported as such. A successful
process exit alone is not a claim that all checks passed; read the result.

## Check the audio match

The digest tool reads the compressed Opus packets without decoding the sound.
This example compares its result with both the manifest and the readable tags:

```bash
python3 - "$CASSINI_FILE" <<'PY'
import sys
from cassini_extract import read_tags, load_manifest
from cassini_digest import compute

path = sys.argv[1]
tags = read_tags(path)
manifest = load_manifest(tags)
actual = compute(path)
claim = manifest["integrity"]
checks = {
    "match policy": claim["matchPolicy"] == tags.get("CASSINI_AUDIO_MATCH_POLICY") == "exact-opus-audio-v1",
    "audio digest": actual["sha256"] == claim["opusAudioSha256"] == tags.get("CASSINI_AUDIO_OPUS_SHA256"),
}
for field, tag in {
    "sampleRate": "CASSINI_AUDIO_SAMPLE_RATE",
    "channels": "CASSINI_AUDIO_CHANNELS",
    "sampleCount": "CASSINI_AUDIO_SAMPLE_COUNT",
    "durationMs": "CASSINI_AUDIO_DURATION_MS",
}.items():
    checks[field] = (
        actual[field] == claim[field] == manifest["audio"][field]
        and str(actual[field]) == tags.get(tag)
    )
checks["meeting duration"] = actual["durationMs"] == manifest["meeting"]["durationMs"]
failed = [name for name, passed in checks.items() if not passed]
if failed:
    sys.exit("Claims do not agree with the audio: " + ", ".join(failed))
print("Audio matches the stored digest and duration/channel claims.")
PY
```

A match establishes the packet identity and shape covered by
[`exact-opus-audio-v1`](/spec/audio-integrity/). If it fails, keep the original
and inspect the named disagreement. A tag/manifest disagreement and an actual
audio mismatch have different [reader states](/consume/#the-six-states).
Do not discard a recovered transcript because the audio changed.

## Validate producer output

When you are making files, also validate the manifest and the selected word
transcript against the schemas. Create an isolated Python environment for the
validator, then download the schemas:

```bash
python3 -m venv .cassini-check
. .cassini-check/bin/activate
python3 -m pip install jsonschema
curl -fLO https://format.gocassini.com/schema/cassini-portable-meeting-manifest-v1.schema.json
curl -fLO https://format.gocassini.com/schema/cassini-words-v1.schema.json
python3 cassini_extract.py "$CASSINI_FILE" > manifest.json
python3 cassini_extract.py "$CASSINI_FILE" --transcript > body.json
python3 - <<'PY'
import json
from jsonschema import Draft202012Validator, FormatChecker

for document, schema in [
    ("manifest.json", "cassini-portable-meeting-manifest-v1.schema.json"),
    ("body.json", "cassini-words-v1.schema.json"),
]:
    with open(schema) as f:
        validator = Draft202012Validator(json.load(f), format_checker=FormatChecker())
    with open(document) as f:
        validator.validate(json.load(f))
    print(document + ": schema valid")
PY
```

For multiple transcripts, repeat body validation for each supported word
transcript using `--transcript ID`. The schemas check structure; requirements
such as one default per slot and valid cross-references also need the
[producer requirements](/spec/v1/#writing-a-file). The extractor's
`--check` does not replace that review.

Before sharing a produced file, open it in the receiving software too. Listen,
seek and review the text. No hash or schema can tell you that the recognizer
heard the right word.

## Implementing these checks in a reader

A producer must write schema-valid data. A reader must also implement the
specification's recovery behavior. For example, a malformed optional
`meeting.recordedAtLocal` should be ignored; it should not make the entire
manifest unavailable. A missing required member is a different case.

Do not turn every JSON Schema error into whole-file rejection. Read the
[state rules](/spec/v1/#trust-and-integrity) and
[extensibility rules](/spec/v1/#extensibility), especially the closed
`integrity` and `payloadRef` objects. Then [test your reader](/build/#check-a-file-then-test-your-implementation)
against both valid and damaged files. Keep the reported state with the data
when passing it to an interface or another application.
