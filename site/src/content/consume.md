Use this guide to get a recording's words, timings and speakers into your own
application. Start with a working reader, use the data, then check what its
reported state establishes. The later sections explain how to implement the
reader yourself.

To listen and read without writing code, [open the browser player](/try/).
For the other implementation paths, see [Build with Cassini](/build/).

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

The reader uses the default transcript. Preserve item order when grouping words
or indexing them: people can overlap, so timestamps can go backwards across a
speaker change. Substituting your own filename is the only change needed to
read another file with a supported word transcript.

## Use the data in JavaScript

The [standalone JavaScript module](https://github.com/codemyriad/cassini-format/blob/main/tools/cassini-read.js)
provides the data independently of the site's interface. See
[the browser integration example](#in-the-browser-with-no-dependencies) for the
complete fetch, read and turn-grouping code. It uses browser APIs and no runtime
dependencies; building an interface is up to your application.

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

[Check a file](/verify/) walks through payload checks, an audio comparison and
schema validation, explaining the scope of each result. To ship your own reader,
also [run the conformance suite](/build/#check-a-file-then-test-your-implementation).

The rest of this guide covers manual inspection and implementation details.
Its shell pipelines need `ffprobe`, `jq`, GNU `basenc`, `awk` and `gunzip`;
those tools are not dependencies of the standalone Python reader. Use your
own file as `meeting.opus`, or substitute `{{demo.filename}}`.

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

A transcript body decodes the same way with its own prefix. This groups
consecutive words by speaker. An overlapping acknowledgment splits the main
speaker's run; Cassini's player reconstructs those fragments as a readable turn
with an inline reply.

```bash
ffprobe -v error -show_entries stream_tags -of json meeting.opus \
| jq -r '.streams[0].tags
         | [to_entries[] | select(.key | test("^{{demo.transcriptPrefix}}[0-9]{3}$"))]
         | sort_by(.key) | map(.value) | join("")' \
| awk '{ p=(4-length($0)%4)%4; printf "%s",$0; for(i=0;i<p;i++) printf "=" }' \
| basenc --base64url -d | gunzip \
| jq -r 'reduce .items[] as $w ([];
           if (.[-1].speaker == $w.speaker)
           then (.[:-1] + [.[-1] + {text: (.[-1].text + " " + $w.text)}])
           else (. + [$w]) end)
         | .[] | "[\(.startMs/1000)s] \(.speaker): \(.text)"'
```

```console
{{demo.turns}}
```

This example uses the demo's `{{demo.transcriptId}}` transcript. A transcript id
is not a format constant: resolve the selected entry's `payloadRef.prefix` from
the manifest when reading other files.

## Getting a model to write the reader

[`/llms-full.txt`](/llms-full.txt) is this whole specification in one text
document: the spec, the body format, the digest contract, both guides, every
schema, and the tag dump of the file the front page links to. Hand it over,
then check the result against [that file](/demo/{{demo.filename}}).

Then check it against the [conformance vectors](/build/#check-a-file-then-test-your-implementation):
A set of fixtures covering edge cases, with a harness that takes a reader in
any language. See [project status](/status/) for implementation and compatibility
notes, and run the suite against the version you plan to ship.

## The algorithm

Eight steps, the same in every language.

1. **Find the OpusTags packet.** Second packet of the logical bitstream. A 60 KB
   comment header spans several Ogg pages, so reassembling across page
   boundaries is the normal path, not an edge case.

2. **Read the comment vector.** Vorbis field names are case-insensitive, so
   upper-case them before comparing, and never touch the value. They are also
   not required to be unique. Cassini never writes a name twice, so a repeat
   means something edited the file: if it is load-bearing — a chunk, a digest, a
   count, `CASSINI_FORMAT` — that is `invalid-cassini-metadata`, and if it is a
   mirror tag, believe the manifest and say you saw it.

3. **Check `CASSINI_FORMAT`.** Absent means plain audio. Accept `/1`. A major
   version you do not implement means play the audio, never error on valid
   Opus.

4. **Reassemble the manifest.** Join `CASSINI_PAYLOAD_000` through
   `CHUNK_COUNT - 1` **by index**, not by the order tags appear. Re-pad,
   base64url-decode, gunzip, parse UTF-8 JSON.

5. **Verify.** SHA-256 the decompressed bytes against `CASSINI_PAYLOAD_SHA256`.
   Bound the decompression while inflating, not after.

6. **Resolve the transcript.** `manifest.transcripts[]` indexes them, each
   entry's `payloadRef` naming its own chunk set and its own SHA-256.

   The manifest resolves the default, not the tag. For each slot — words,
   display — take the first entry for that slot flagged
   `default: true`, and failing that the first entry for that slot in array
   order. `CASSINI_TRANSCRIPT_DEFAULT` is a copy; ignore it when it names
   nothing the manifest has, and say so when it disagrees with the flag.

   Every entry in `transcripts[]` participates. Do not filter or rank words by
   a `role` label; older files may carry one, and newer ones omit it. For
   display, use a `role: "display"` entry from `readableTranscripts[]` whose
   `sourceTranscriptId` matches the selected words. Skip withdrawn cleanup
   entries and bodies whose format your reader does not implement.

7. **Read the items in file order.** They are in speaker-turn order, not sorted
   by time: across a speaker change `startMs` goes backwards, because people
   talk over each other. Sorting by `startMs` destroys every turn. A turn is a
   maximal run of consecutive items with the same `speaker`, which is what the
   `jq` above reconstructs in one pass.

8. **Ignore what you do not recognise.** A tag name or a manifest member you
   have never heard of is not an error, at any depth. The two exceptions are
   `integrity` and every `payloadRef`, where every member is an instruction and
   an unknown one is a verification failure.

## In the browser, with no dependencies

Download the module alongside your application's JavaScript:

```bash
curl -fLO https://raw.githubusercontent.com/codemyriad/cassini-format/main/tools/cassini-read.js
```

`fetch` gets the bytes, `DecompressionStream` inflates, `crypto.subtle` checks
the digests. The player on the front page uses this module to read the downloadable
file, then displays it with Cassini’s transcript component.

[`tools/cassini-read.js`](https://github.com/codemyriad/cassini-format/blob/main/tools/cassini-read.js)
is that module, CC0, generated from the site's own reader. The transcript interface
is a separate AGPL-3.0 component from Cassini; it displays short interjections
inline and highlights the active turn or interjection during playback.
`tools/cassini-read-pure.py` does the same in
Python with no external tools, and only ever reads the front
of the file — the same code works over an HTTP range request.

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
`crypto.subtle` requires a secure context. Opening an HTML file directly from
disk is not the same as serving the application. Browser support for audio
playback is separate from support for reading the metadata.

`state` comes back alongside the data, one of the six below. `verified:
{ manifest, transcript }` says what was checked: `true` matched, `null` nothing
claimed one, `false` disagreed. A manifest that disagrees is not shown at all;
a transcript that disagrees comes back as `unavailable` with the reason.

## The six states

Every read ends in exactly one of six states, and the names are part of the
spec so that two readers describe one file the same way:

| state | what you found | what you do |
|---|---|---|
| `plain-audio` | no `CASSINI_FORMAT` | play it, silently, not an error |
| `unknown-cassini-format` | a major version you do not implement | play it, say the metadata is newer than you |
| `invalid-cassini-metadata` | tags present, payload won't reassemble, decode or hash | play it, say which step failed |
| `unverified` | readable, audio not checked | show the transcript, marked unverified |
| `stale-audio` | readable, checked, does not match | show the transcript, labelled, offer plain audio |
| `ok` | readable, checked, matches | open it as a meeting |

Three digests, three different consequences:

* The **manifest** digest fails: the manifest is not used, not even a field of
  it. `invalid-cassini-metadata`; the audio plays.
* A **transcript body** digest fails: that transcript is unavailable. The
  meeting, the speakers and the other transcripts are still good, and the
  file's state does not change.
* The **audio** digest fails: keep the transcript and label it. `stale-audio`
  is what happens when a file is reprocessed or remuxed, which is the normal
  life of one. Discarding the transcript here is the one thing a reader must
  not do.

If you never verify the audio, you are still conforming: a reader that pulls
only the front of the file over a range request cannot. Report `unverified`.
The one thing the spec forbids outright is claiming a check you did not run.

## Things that will trip you up

* **Padding.** Producer writes unpadded, the Go reader rejects padded, the
  spec's own example re-pads. Accept both.
* **Chunk order.** Reassemble by index. The producer writes tags ASCII-sorted,
  which puts `CASSINI_PAYLOAD_000` nowhere near where you would expect.
* **`CASSINI_FORMAT` is comment nine, not comment one.** No magic bytes at a
  fixed offset.
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
