You have a `.opus` file and you want the transcript out of it. Everything you
need is in the file.

## Is this one of those files?

```bash
ffprobe -v error -show_entries stream_tags=CASSINI_FORMAT \
        -of default=nw=1:nk=1 meeting.opus
```

```console
org.cassini.portable-meeting/1
```

Nothing printed means ordinary audio. That is an answer, not an error.

Two traps. Ogg carries comments on the *stream*, so `-show_entries format_tags`
returns nothing. And `ffprobe` renames `DESCRIPTION` to `comment`.

## The payload, in one pipeline

No script, no library:

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

A transcript body decodes the same way with its own prefix. This reconstructs
the meeting as speaker turns:

```bash
ffprobe -v error -show_entries stream_tags -of json meeting.opus \
| jq -r '.streams[0].tags
         | [to_entries[] | select(.key | test("^CASSINI_TX_RAW_ASR_PAYLOAD_[0-9]{3}$"))]
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

`raw-asr` is a transcript id, not a constant. Read `CASSINI_TRANSCRIPT_IDS` and
`CASSINI_TRANSCRIPT_DEFAULT`, or read the manifest, which is the record.

## Getting a model to write the reader

Better than waiting for me to write one in your language.
[`/llms-full.txt`](/llms-full.txt) is this whole specification in one 100 KB
document: errata first, then the spec, the body format, the digest contract, both
guides, every schema, and the real tag dump of the file the front page links to.
Hand it over, then check the result against
[that file](/demo/lantern-festival.opus).

The errata come first on purpose. They are short, and they are where the
reference readers still disagree with the spec — padding, the inflate bound, the
state names — so a model reading them knows which side to implement. If
something written from the bundle still gets it wrong, that is a bug in the
bundle and I want to hear about it.

Then check it against the [conformance vectors](https://github.com/codemyriad/cassini-format/tree/main/spec/conformance):
22 files covering the edges, with a harness that takes a reader in any language.
The three readers in this repository pass with no hard failures. The reference Go
implementation has three, two of them on files these readers decode fine, which
is what a suite is for.

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
   mirror tag, believe the manifest and say you saw it. Both current readers
   assume names are unique and upper-case, and have got away with it because the
   producer writes them that way.

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
   readable, display — take the first entry for that slot flagged
   `default: true`, and failing that the first entry for that slot in array
   order. `CASSINI_TRANSCRIPT_DEFAULT` is a copy; ignore it when it names
   nothing the manifest has, and say so when it disagrees with the flag.

7. **Read the items in file order.** They are in speaker-turn order, not sorted
   by time: across a speaker change `startMs` goes backwards, because people
   talk over each other. Sorting by `startMs` destroys every turn. A turn is a
   maximal run of consecutive items with the same `speaker`, which is what the
   `jq` above reconstructs in one pass.

8. **Ignore what you do not recognise.** A tag name or a manifest member you
   have never heard of is not an error, at any depth. The two exceptions are
   `integrity` and every `payloadRef`, where every member is an instruction and
   an unknown one is a verification failure. The schemas now say exactly that.

## In the browser, with no dependencies

`fetch` gets the bytes, `DecompressionStream` inflates, `crypto.subtle` checks
the digests. The player on the front page is this module reading the file you can
download.

`tools/cassini-read.js` is that module, CC0, about 300 lines. It is generated
from the site's own reader and the build fails if they drift, so the file you
download is the one this page ran. `tools/cassini-read-pure.py` does the same in
Python with no external tools, in about 110 lines, and only ever reads the front
of the file — the same code works over an HTTP range request.

```js
import { readCassini, toTurns } from './cassini-read.js';

const buf = await (await fetch('meeting.opus')).arrayBuffer();
const file = await readCassini(buf);

if (file.cassini) {
  const turns = toTurns(file.transcript.words, file.manifest.speakers);
  console.log(file.manifest.meeting.title, turns.length, 'turns');
}
```

`verified: { manifest, transcript }` comes back alongside the data. `true` means
the digest matched, `null` means nothing claimed one, `false` means it
disagreed. That last one is not a reason to throw anything away.

## Say which of the six states you ended in

**Keep the transcript. Label it. Let the person decide.**

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

Discarding the transcript is never one of the answers. The rule that used to say
so was written to catch edited audio, and that is not what happens to these
files: the audio stays put and the transcript gets replaced, because
reprocessing with a better model is the normal life of one. It fired on every
shipped v1 file over a 312-sample pre-skip.

If you never verify the audio, you are still conforming — a reader that pulls
only the front of the file over a range request cannot. Report `unverified` and
mean it. The one thing the spec forbids outright is claiming a check you did not
run.

The digest catches accidents: a transcript reattached to the wrong audio, a
corrupted payload, a truncated download. Not someone who wants to lie to you.

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
* **A very large comment header may arrive incomplete.**
  [RFC 7845 §5.2](https://www.rfc-editor.org/rfc/rfc7845#section-5.2) lets you
  ignore comments past the first 61,440 octets, and ASCII sorting can push the
  descriptors past that line on a long recording. If `CHUNK_COUNT` is missing on
  a file that plainly has chunk tags, this is why. Count the tags you can see,
  and say that you did.
* **The summary tags are an incomplete copy.** A file carries no
  `CASSINI_WORD_COUNT`, no `CASSINI_TRANSCRIPT_LANGUAGE`, no `CASSINI_STT_*`,
  whatever the spec says. Read the manifest.
