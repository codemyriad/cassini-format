Use this guide to turn existing audio and timed words into a file someone else
can open. First package the example, then substitute your own inputs and check
the result before sharing it.

You need **Python 3 and curl** for the first example. The producer uses only
the Python standard library. Recording, speech recognition and any audio
conversion happen before this step.

## Write your first file

In a fresh directory, download the [CC0 producer](https://github.com/codemyriad/cassini-format/blob/main/tools/cassini-pack.py),
the example audio and its matching word data:

```bash
curl -fLO https://raw.githubusercontent.com/codemyriad/cassini-format/main/tools/cassini-pack.py
curl -fLO https://format.gocassini.com/demo/{{demo.filename}}
curl -fLO https://format.gocassini.com/demo/{{demo.wordInput}}
python3 cassini-pack.py {{demo.filename}} {{demo.wordInput}} meeting.opus \
  --title "My portable recording" --created-at 2026-09-09T09:00:00Z
```

The result is `meeting.opus`, containing **{{demo.words}} words** and
**{{demo.speakers}} speakers**. The command prints `audio digest unchanged`
after reading back the output and comparing the compressed audio with the input.
[Open the result](/try/) to read and listen to your newly packaged file.

The sample source already has Cassini metadata. This exercise uses its audio
and supplies the words again. The packer writes a new manifest from the supplied
inputs; it does not merge existing transcripts or other metadata from the source.

## Use your own inputs

Replace the audio and JSON paths, title and date in the command. Your source
must be Ogg Opus. Your JSON supplies the speaker table and the words that
actually describe that recording:

```json
{
  "speakers": [{ "id": "sam", "label": "Sam" }],
  "items": [
    { "speaker": "sam", "startMs": 900, "endMs": 1300, "text": "Hello." }
  ]
}
```

Times are integer milliseconds from the start of the audio. Each word's
`speaker` identifies an entry in `speakers`. Keep words in speaker-turn order,
including overlaps; sorting the whole list by time changes how conversations
are reconstructed. See the [word format](/spec/words-v1/) for exact rules.

The packer also accepts `segments` instead of `items`:

```json
{
  "speakers": [{ "id": "sam", "label": "Sam" }],
  "segments": [
    { "speaker": "sam", "words": [
      { "startMs": 900, "endMs": 1300, "text": "Hello." }
    ] }
  ]
}
```

Use these exact field names and millisecond units when adapting speech-recognition
output. This is a supported JSON input shape, not a general importer for every
transcription service. Speaker attribution and transcription accuracy remain
the responsibility of the pipeline that supplied them.

## Check and share the result

The producer's self-check establishes that packaging preserved the audio digest.
Before sharing, [validate the output](#checking-your-work) and open the result in
the recipient's software. An ordinary Ogg Opus player can play it; a Cassini
reader can also show the embedded transcript.

## What you are making

An Ogg Opus file at 48 kHz, mono for speech, with two things in its OpusTags
comment header: plain comments a human can read, and a JSON manifest gzipped,
base64url-encoded and cut into numbered pieces.

<!-- TODO(chris): wording -->
What a producer MUST do is normative and not restated here: the container and
digest rules are in [Writing a file](/spec/v1/#writing-a-file), and every tag a
file has to carry, with its exact value, is in
[Cassini descriptor tags](/spec/v1/#cassini-descriptor-tags).

<!-- TODO(chris): wording -->
Beyond that, the reference producer writes readable `TITLE`, `DATE` and
`DESCRIPTION` comments, writes a summary tag only when it has a value, and never
puts a room token, join link or internal service URL in a tag, because these
files get mailed to people; see
[Summary and mirror tags](/spec/v1/#summary-and-mirror-tags).

## A complete producer

`tools/cassini-pack.py` builds a valid file with nothing but the Python
standard library. No ffmpeg, no Go. It walks the Ogg pages, computes the digest,
builds the manifest, and rewrites only the `OpusTags` packet, copying every audio
page across untouched and patching the page sequence numbers and CRCs.

The digest excludes `OpusTags` and all Ogg framing, so tagging cannot change
it: compute it once.

`tools/cassini-opus-digest.py` computes `exact-opus-audio-v1` from
[the digest spec](/spec/audio-integrity/) alone.
[Check the audio match](/consume/#check-the-audio-match) shows how to download it
and compare the result with the claims in a file. For the downloadable example,
the computed digest and the stored claim agree:

```console
{{demo.audioDigest}}
```

The file contains {{demo.sampleCount}} playable samples at {{demo.sampleRate}} Hz,
for a duration of {{demo.durationMs}} ms. These values and the digest above are
read from the downloadable file when the site is generated.

## Checking your work

When you are making files, validate the manifest and the selected word
transcript against the schemas. The commands need **Python 3, curl and ffprobe**
(part of FFmpeg), and one Python package in an isolated environment:

```bash
python3 -m venv .cassini-check
. .cassini-check/bin/activate
python3 -m pip install jsonschema
curl -fLo cassini_extract.py https://raw.githubusercontent.com/codemyriad/cassini-format/main/tools/cassini-extract.py
curl -fLO https://format.gocassini.com/schema/cassini-portable-meeting-manifest-v1.schema.json
curl -fLO https://format.gocassini.com/schema/cassini-words-v1.schema.json
python3 cassini_extract.py meeting.opus > manifest.json
python3 cassini_extract.py meeting.opus --transcript > body.json
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
transcript using `--transcript ID`.

The schemas check structure. Also review the cross-field rules: one default
per slot, valid `sourceTranscriptId` references, and agreement between the
manifest and summary tags. Passing a schema or the extractor's `--check` alone
does not establish those rules. The [normative producer requirements](/spec/v1/#writing-a-file)
remain the contract.

Before sharing a produced file, open it in the receiving software too. Listen,
seek and review the text. No hash or schema can tell you that the recognizer
heard the right word.
