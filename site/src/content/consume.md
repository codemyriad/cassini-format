Use this guide to get a recording's words, timings and speakers into your own
application. Start with a working reader, use the data, then check what its
reported state establishes.

## Read your first file

You need Python 3 and `curl`. Download the CC0 reader and the same example used
on this site, then run it:

```bash
curl -fLO https://raw.githubusercontent.com/codemyriad/cassini-format/main/tools/cassini-read-pure.py
curl -fLO https://format.gocassini.com/demo/{{demo.filename}}
python3 cassini-read-pure.py {{demo.filename}}
```

The output includes the title, transcript availability and the first few words
with their timestamps. The state is `unverified`: this reader verifies the
metadata digests but does not check the audio digest. It uses only the Python
standard library.

## Use the data in Python

The command above is a preview. For an integration, download the same reader
under an importable name and write the full data to `transcript.json`:

```bash
curl -fLo cassini_reader.py https://raw.githubusercontent.com/codemyriad/cassini-format/main/tools/cassini-read-pure.py
python3 - {{demo.filename}} <<'PY'
import json
import sys
from cassini_reader import read_file

result, _ = read_file(sys.argv[1])
if not result.get("manifest") or result.get("words") is None:
    sys.exit("No usable word transcript: " + result["state"] + " " + str(result.get("notes", [])))
manifest = result["manifest"]
speakers = {speaker["id"]: speaker["label"] for speaker in manifest["speakers"]}
words = [
    {**word, "speakerLabel": speakers.get(word["speaker"], "Unknown speaker")}
    for word in result["words"]
]
with open("transcript.json", "w", encoding="utf-8") as output:
    json.dump({"state": result["state"], "title": manifest["meeting"]["title"],
               "transcriptId": result["default"], "speakers": manifest["speakers"],
               "items": words}, output, ensure_ascii=False, indent=2)
print(f"Wrote {len(words)} words to transcript.json; state: {result['state']}")
PY
```

The example yields **{{demo.words}} words** from **{{demo.speakers}} speakers**.
Each item retains its original `speaker`, `startMs`, `endMs` and `text`, with a
`speakerLabel` added for your interface. Keep that ID alongside the label: names
are for display, IDs identify speakers. `speakerLabel` here is an application
field, not a new format requirement.

The reader uses the default transcript. Substituting your own filename is the
only change needed to read another file with a supported word transcript.

## Use the data in JavaScript

The [standalone JavaScript module](https://github.com/codemyriad/cassini-format/blob/main/tools/cassini-read.js)
provides the data independently of the site's interface. It uses browser APIs and
no runtime dependencies; building an interface is up to your application.
`fetch` gets the bytes, `DecompressionStream` inflates, `crypto.subtle` checks
the digests.

```js
import { readCassini, toTurns } from './cassini-read.js';

const response = await fetch('meeting.opus');
if (!response.ok) throw new Error(`Could not load recording: ${response.status}`);
const buf = await response.arrayBuffer();
const file = await readCassini(buf);

if (file.manifest && file.transcript) {
  const turns = toTurns(file.transcript.words, file.manifest.speakers);
  console.log(file.manifest.meeting.title, turns.length, 'turns');
}
console.log(file.state); // Preserve this status in your viewer.
```

Serve this code and `meeting.opus` from your application's HTTP server and
run it as a JavaScript module. Use HTTPS in production (localhost also works):
`crypto.subtle` requires a secure context.

## Choose another transcript

A file can contain several transcripts. The default is the first entry in
`manifest.transcripts` flagged `default: true`, or the first entry if none is
flagged. Your application can offer the other supported entries as alternatives.

For command-line extraction of a particular transcript, use the CC0 extractor.
This alternative needs **ffprobe** (part of FFmpeg) as well as Python 3:

```bash
curl -fLO https://raw.githubusercontent.com/codemyriad/cassini-format/main/tools/cassini-extract.py
python3 cassini-extract.py {{demo.filename}} --list
python3 cassini-extract.py {{demo.filename}} --transcript {{demo.transcriptId}} > selected-transcript.json
```

Use an ID printed by `--list` for your own file. The output is the selected
body, including `items`; the speaker table belongs to the manifest, which the
extractor prints when run without `--transcript`.

## Check your result

Opening a transcript establishes that the reader could recover its data. The
examples above report `unverified` because they do not compute the audio match.
Keep that state with the data. It must not become a claim of verified audio
when you pass the words to another part of your application.

<!-- TODO(chris): wording -->
<!-- The id below only keeps /verify/'s link alive; delete it with that page. -->
<span id="the-six-states"></span>
Every read ends in exactly one of six states. They are named and defined, with
the consequence of each failing digest, in
[the specification](/spec/v1/#trust-and-integrity).

The two checks below use **Python 3, curl and ffprobe** (part of FFmpeg). Run
them in the same directory so the downloaded modules can be imported. Use your
own file as `meeting.opus`, or substitute `{{demo.filename}}`. To ship your own
reader, also [run the conformance suite](/build/#check-a-file-then-test-your-implementation).

### Check the embedded data

```bash
curl -fLo cassini_extract.py https://raw.githubusercontent.com/codemyriad/cassini-format/main/tools/cassini-extract.py
python3 cassini_extract.py meeting.opus --check
```

For a readable Cassini file this prints `ok` for the manifest and each decoded
transcript. A missing chunk, damaged payload or mismatched digest stops the
check with an explanation. This checks payload bytes, not every semantic rule
in the specification, and ffprobe merges duplicate comment names, so it cannot
detect every duplicate-tag error.

### Check the audio match

The digest tool reads the compressed Opus packets without decoding the sound.
Compute the digest, then compare it with the one the file claims:

```bash
curl -fLO https://raw.githubusercontent.com/codemyriad/cassini-format/main/tools/cassini-opus-digest.py
python3 cassini-opus-digest.py meeting.opus
ffprobe -v error -show_entries stream_tags=CASSINI_AUDIO_OPUS_SHA256 \
        -of default=nw=1:nk=1 meeting.opus
```

The `sha256` the first command prints must equal the tag the second one prints.
A match establishes the packet identity and shape covered by [`exact-opus-audio-v1`](/spec/audio-integrity/). If it
fails, keep the original and inspect the disagreement. Do not discard a
recovered transcript because the audio changed.

<!-- TODO(chris): wording -->
The rest of this guide is manual inspection, for looking at a file by hand. Its
shell pipelines also need `jq`, GNU `basenc`, `awk` and `gunzip`; those tools
are not dependencies of the standalone Python reader.

## Is this one of those files?

```bash
ffprobe -v error -show_entries stream_tags=CASSINI_FORMAT \
        -of default=nw=1:nk=1 meeting.opus
```

```console
org.cassini.portable-meeting/1
```

Nothing printed means ordinary audio.

Two traps. Ogg carries comments on the *stream*, so `-show_entries format_tags`
returns nothing. And `ffprobe` renames `DESCRIPTION` to `comment`.

## The payload, in one pipeline

No script, no library. This is for looking, not for a reader: it takes the
chunks it can see, three digits only, and checks nothing. A reader joins exactly
`CHUNK_COUNT` chunks by index and verifies the digest.

```bash
ffprobe -v error -show_entries stream_tags -of json meeting.opus \
| jq -r '[.streams[0].tags | to_entries[]
          | select(.key | test("^CASSINI_PAYLOAD_[0-9]{3}$"))]
         | sort_by(.key) | map(.value) | join("")' \
| awk '{ p=(4-length($0)%4)%4; printf "%s",$0; for(i=0;i<p;i++) printf "=" }' \
| basenc --base64url -d | gunzip | jq .
```

The `awk` line re-pads: the producer writes unpadded base64url, GNU `basenc`
demands padding.

## Things that will trip you up

* **Padding.** Producer writes unpadded, the Go reader rejects padded, the
  spec's own example re-pads. Accept both.
* **Chunk order.** Reassemble by index. The producer writes tags ASCII-sorted,
  which puts `CASSINI_PAYLOAD_000` nowhere near where you would expect.
* **`CASSINI_FORMAT` is comment nine, not comment one.** No magic bytes at a
  fixed offset.
* **Items are in speaker-turn order, not sorted by time.** Across a speaker
  change `startMs` goes backwards, because people talk over each other. Sorting
  by `startMs` destroys every turn.
* **Transcript ids map to prefixes by upper-casing and replacing `-` with `_`.**
  So `raw-asr` and `raw_asr` collide. Do not use `_`.
* **`CASSINI_TRANSCRIPT_IDS` is sorted; `manifest.transcripts[]` is not.** Same
  ids, different order. Neither is wrong.
* **A comment header can be large.**
  [RFC 7845 §5.2](https://www.rfc-editor.org/rfc/rfc7845#section-5.2) lets a
  generic reader ignore comments past the first 61,440 octets. A Cassini reader
  may not: on a long recording the tags that make the file decodable sit past
  that mark. Read the whole `OpusTags` packet, and over HTTP fetch more until
  you have it.
* **The summary tags are an incomplete copy.** Word count, language and the
  speech-to-text engine are only in the manifest. Read the manifest.

<!-- TODO(chris): wording -->
The step-by-step reading algorithm is normative and lives in
[the specification](/spec/v1/#reading-a-file). Every tool named above is listed,
with its language and licence, on the [tools page](/build/).
