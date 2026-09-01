# Cairn (public page draft)

Date: 2026-08-28
Source: <https://silvio-cassini-format-freeze.pgs.sh/format.html>
Status: draft of the format's future public site, written while the format is
still being finalized. "Cairn" is a working name; see [naming.md](naming.md).

Kept here because it is the best plain-language description of the format that
exists, and because the site it was drafted for does not exist yet.

---

## One ordinary audio file that carries its own transcript.

A Cairn file is a normal `.opus` audio file that also holds, in its own
metadata, everything needed to reopen the recording as a document: who spoke,
what they said, word by word with timestamps, and how that transcript was
produced. To an audio player it is just audio. Nothing about the file looks
unusual until you go looking.

There is no new codec, no new extension, no new media type. The container is
Ogg, the audio is Opus, the media type is `audio/ogg`, and the transcript rides
in the OpusTags comment header, the same place `TITLE` and `ARTIST` live. A tool
that has never heard of Cairn plays the audio and ignores the rest. That is the
whole trick.

Cairn is the working name. The format grew inside Cassini, a meeting recorder
for Nextcloud Talk, and is being spun out as an independent format. Files packed
before the rename use `CASSINI_` wherever this page says `CAIRN_`, and identify
themselves as `org.cassini.portable-meeting/1` or `/2`. Readers should accept
both spellings.

## See for yourself

Everything below is readable with stock tools. The tags alone already tell you
what you are holding:

```console
$ ffprobe -v error -show_entries stream_tags -of default=nw=1 meeting.opus
TAG:CAIRN_FORMAT=cairn/2
TAG:CAIRN_PAYLOAD_ENCODING=base64url+gzip+utf8json
TAG:CAIRN_PAYLOAD_CHUNK_COUNT=2
TAG:CAIRN_PAYLOAD_000=H4sIAAAAAAAA…          (the manifest, in numbered chunks)
TAG:CAIRN_SPEAKER_COUNT=5
TAG:CAIRN_TRANSCRIPT_IDS=parakeet
TAG:CAIRN_TRANSCRIPT_DEFAULT=parakeet
TAG:CAIRN_TX_PARAKEET_PAYLOAD_000=H4sIAAAA…  (a transcript body, own chunks)
TAG:CAIRN_DECODE_HINT=Concatenate CAIRN_PAYLOAD_000..N, base64url decode, …
```

And the payload decodes in one pipeline. This is the actual command, run against
a real file, not pseudocode:

```bash
ffprobe -v error -show_entries stream_tags -of json meeting.opus \
| jq -r '[.streams[0].tags | to_entries[]
          | select(.key | test("^CAIRN_PAYLOAD_[0-9]{3}$"))]
         | sort_by(.key) | map(.value) | join("")' \
| awk '{ p=(4-length($0)%4)%4; printf "%s",$0; for(i=0;i<p;i++) printf "=" }' \
| basenc --base64url -d | gunzip | jq .
```

(The payload is unpadded base64url; the awk line re-pads it because GNU `basenc`
insists on padding. A transcript body decodes the same way with its own prefix,
`CAIRN_TX_PARAKEET_PAYLOAD_`.)

## The shape of the file

The metadata has two layers, on purpose.

The first layer is plain tags any tool can show: title, date, speaker count,
word count, and a decode hint that explains the second layer in one sentence. I
want a curious person with `ffprobe` and no documentation to be able to work the
format out on their own.

The second layer is the payload: compact UTF-8 JSON, gzip-compressed,
base64url-encoded, split across numbered tags (`CAIRN_PAYLOAD_000`, `001`, …)
kept small (4096 characters by default) so the comment header stays inspectable
in ordinary tools. Chunks reassemble by tag index, not by the order they appear
in the file. Why gzip and not something denser: a browser can inflate gzip
natively, and at this payload size (the 17-minute sample file carries 62 KB of
compressed payload) the difference doesn't matter.

## The manifest

The decoded payload is one JSON object, validated by a JSON Schema (today the
schemas live in the Cassini repo; serving them from permanent URLs is part of
the freeze proposal). Abridged:

```jsonc
{
  "kind": "cairn",
  "version": 2,
  "profile": "ogg-opus",
  "meeting": { "id": "mtg_213e1a45…", "title": "daily meeting",
               "recordedAtLocal": "2026-03-10T12:30:00+01:00",
               "createdAtUtc": "2026-03-19T05:58:23Z",   // when it was packed
               "durationMs": 1046260 },
  "audio": { "codec": "opus", "sampleRate": 48000, "channels": 1 },
  "integrity": { "digest": "213e1a45…" },
  "speakers": [ { "id": "speaker_0", "label": "Ana" } ],
  "transcripts": [
    { "id": "parakeet", "role": "raw-asr", "default": true,
      "format": "words/1", "language": "en",
      "payloadRef": { "chunkCount": 14, "sha256": "…",
                      "encoding": "base64url+gzip+utf8json" } }
  ],
  "provenance": { "speechToText": { "parakeet": { "engine": "…", "model": "…",
                                                  "version": "…" } } }
}
```

| field | what it holds |
|---|---|
| `meeting` | what a listing needs before decoding anything else: id, title, when it was recorded, when it was packed, how long |
| `audio` | what is actually stored: codec, sample rate, channels, duration |
| `integrity` | the audio digest that binds transcript to recording |
| `speakers` | stable ids the transcript entries point at, with display labels |
| `transcripts` | the index of transcript bodies; the bodies live in their own chunk sets |
| `provenance` | which engine, model and producer version made each layer |

## Several transcripts, one recording

A file can carry more than one transcript of the same audio: raw ASR next to a
human-corrected pass, two engines side by side, a cleaned-up readable version
next to the verbatim one. Each body lives in its own chunk set with its own
SHA-256, under a prefix derived from the transcript's id (`parakeet` →
`CAIRN_TX_PARAKEET_PAYLOAD_000`…); the manifest holds the index. One entry in
each family (verbatim, readable, display) can be marked `default`; that is the
one a reader shows first.

A body is as plain as the rest, one item per word:

```json
{ "format": "words/1", "language": "en",
  "items": [
    { "speaker": "speaker_0", "startMs": 120437, "endMs": 120597, "text": "I" }
  ] }
```

`speaker` points at the manifest's `speakers[].id`, and the millisecond offsets
are what let a reader jump the audio to any word.

Derived transcripts (a readable cleanup, a display version) always name the raw
transcript they came from, and the raw ASR is always kept even when a cleaned
version exists, because a better cleanup model will come along and it will want
the original to work from. If information might enable better processing later,
keep it.

## The audio digest

Every file carries a SHA-256 of its Opus audio packets, concatenated in stream
order (the header and comment packets are skipped, so rewriting tags doesn't
change it; the spec pins the exact byte rule, multi-stream files included). It
answers exactly one question: is this transcript describing this recording?

The meeting id is derived from the same digest. That is what keeps identity
stable across the format's normal lifecycle: transcribe a recording again next
year with a better model, and the file you pack is still, verifiably, the same
meeting.

What the digest is not: proof of authenticity. Anyone who rewrites the
transcript can recompute every hash, and the file will verify. The digest
catches accidents (a transcript reattached to the wrong audio, a corrupted
payload), not adversaries. A reader that finds a digest disagreeing with the
audio keeps the transcript, labels it unverified, and lets the human decide.

## Why not a sidecar?

The obvious objection first, because it is a good one: the ecosystems next door
keep transcripts out of band. Podcasting 2.0 links transcript files from the
feed. Speech research passes CTM and RTTM files around. And out-of-band is
genuinely more flexible: you can fix a transcript without touching the audio
file at all.

But sidecars get separated. A file that leaves its archive (mailed, moved to a
phone, dropped in a chat) arrives alone, and the transcript is gone. Cairn
optimizes for the file that travels. Everything is in the one file, and the file
stays playable at every stop along the way. Fixing a transcript without touching
the audio still works, too: you rewrite the tags, and the audio packets (and the
identity derived from them) don't move.

## What Cairn doesn't do

It doesn't model transcript history. A reprocessed file replaces its
predecessor; provenance records what made the current transcript, not what came
before.

It doesn't promise to survive audio edits made by Cairn-unaware tools. Cut the
audio in an editor and the digest no longer matches; the file is then a plain
recording with stale metadata.

It doesn't prove authenticity. See above.

It doesn't claim a file extension or a media type. The file is `audio/ogg`, and
that is the point.

## Versions and compatibility

The format id is `cairn/2`. There is deliberately no `cairn/1`: versions 1 and 2
were spent while the format lived inside Cassini, as
`org.cassini.portable-meeting/1` and `/2`, and files with those ids exist.
`cairn/2` is the same manifest shape as `org.cassini.portable-meeting/2` with
the prefix renamed; readers treat the old identifiers as aliases and read all
three.

(Note added 2026-09-01: `org.cassini.portable-meeting/1` shipped the day after
this was written, so the numbering here needs redeciding. See freeze item 6.)

Readers ignore tags and manifest members they don't recognise. A reader that
meets a major version it doesn't implement falls back to playing the audio; it
never errors on a valid Opus file.

## Status

Draft. Cassini is the only implementation so far (producer and reader,
AGPL-3.0). The spec text will be CC-BY-4.0 and the schemas and test vectors CC0,
so anyone can implement the format without asking anyone's permission, which is
the point of writing it down.

The decode pipeline above was run against a real (pre-rename) file, with
`CASSINI_` in place of `CAIRN_`, before it went on this page.
