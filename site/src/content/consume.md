Start with the standalone reader to see what a file contains, then use the
algorithm below to build your own. To listen and explore without writing code,
[open the browser reader](/try/).

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

For JavaScript, jump to [the browser reader](#in-the-browser-with-no-dependencies).
The shell examples below use `ffprobe`, `jq`, GNU `basenc`, `awk` and `gunzip`.
Use your own file as `meeting.opus`, or substitute `{{demo.filename}}`.

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

Then check it against the [conformance vectors](https://github.com/codemyriad/cassini-format/tree/main/spec/conformance):
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

const buf = await (await fetch('meeting.opus')).arrayBuffer();
const file = await readCassini(buf);

if (file.manifest && file.transcript) {
  const turns = toTurns(file.transcript.words, file.manifest.speakers);
  console.log(file.manifest.meeting.title, turns.length, 'turns');
}
console.log(file.state); // Preserve this status in your viewer.
```

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
