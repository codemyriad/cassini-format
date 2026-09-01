# cassini-format

A Cassini portable meeting is an ordinary `.opus` file. Double-click it and any
audio player plays it, because that is all it is: Ogg Opus, 48 kHz. But it also
carries the full word-timestamped transcript, the speakers, and a record of
which models produced what, embedded in the OpusTags where players that don't
care will simply ignore them.

This repository is the specification and the schemas. The implementation lives
in [gocassini](https://github.com/codemyriad/gocassini), which records,
transcribes and packs these files. The two were the same repo until now; I split
the format out because a format that only one program can read isn't really a
format.

Try it on a file:

```bash
tools/cassini-extract.py meeting.opus --tags     # the descriptor tags
tools/cassini-extract.py meeting.opus --list     # which transcripts are inside
tools/cassini-extract.py meeting.opus            # the whole manifest as JSON
```

That script is about 150 lines of Python and it shells out to `ffprobe`. It
doesn't import anything Cassini-specific, on purpose: if the format is really
self-describing, a reader should be writable from the tags alone. Consider it
both a tool and a conformance check.

## what's here

* [`SPEC.md`](SPEC.md) — the format, v1 through v3, with the rationale and the
  rejected alternatives kept in place
* [`spec/`](spec/) — the JSON Schemas for the manifest (v1, v2, v3), plus
  [`cassini-opus-audio-integrity-v1.md`](spec/cassini-opus-audio-integrity-v1.md),
  the byte-level definition of the audio digest
* [`design/`](design/) — how we got here: the multi-transcript proposal that
  became v2, and a research brief that is still open (see below)
* [`tools/`](tools/) — the reference extractor

## the shape of it, in one screen

Metadata rides in two layers. The first is plain Vorbis comments a human can
read in `ffprobe` output (`TITLE`, `CASSINI_SPEAKER_COUNT`, `CASSINI_STT_MODEL`,
and so on). The second is a JSON manifest, gzipped, base64url-encoded, and split
across numbered tags:

```text
CASSINI_FORMAT=org.cassini.portable-meeting/3
CASSINI_PAYLOAD_ENCODING=base64url+gzip+utf8json
CASSINI_PAYLOAD_CHUNK_COUNT=52
CASSINI_PAYLOAD_SHA256=743fc2d2...
CASSINI_DECODE_HINT=Concatenate CASSINI_PAYLOAD_000..N, base64url decode, gzip decompress, parse UTF-8 JSON.
CASSINI_PAYLOAD_000=H4sIAAAAAAAAA6y9XZPsxpEl-F...
```

`CASSINI_DECODE_HINT` is there because I wanted someone poking at one of these
files with `ffprobe` and no documentation to still get the transcript out. It is
not load-bearing for any consumer. It's a message in a bottle.

Three design commitments run through the whole thing:

* **Progressive enhancement.** If a player understands nothing, it still plays
  the audio. If a reader understands the tags, it gets everything.
* **Keep what a better model could use later.** The raw ASR words survive even
  after an LLM cleans them up, along with the provenance saying which engine,
  which model, which device produced each layer. The cleanup of 2026 will look
  bad in 2028; the timestamps won't.
* **Fail closed on edited audio.** The manifest carries a digest of the audio.
  Edit the audio and leave the old transcript attached, and a conforming
  consumer must tell the user the transcript is stale rather than show it
  silently drifting.

That last one is where v3 differs from v1 and v2. v1 hashed decoded PCM, which
meant a consumer had to decode the entire file to check identity, and any
re-encode broke it. v3 hashes the compressed Opus packets instead, with a
canonical byte stream defined in
[`spec/cassini-opus-audio-integrity-v1.md`](spec/cassini-opus-audio-integrity-v1.md).
It deliberately excludes `OpusTags`, because otherwise writing the digest into
the file would change the digest. v2, in between, is what let one file hold
several transcripts of the same audio (parakeet next to canary, raw next to
human-corrected) without duplicating the recording.

## status, honestly

v3 is what the producer writes today, and it is stable in the sense that we run
it in production and read the files back. It is not stable in the sense of being
a standard anyone else has agreed to. The URLs in `CASSINI_PAYLOAD_SCHEMA` still
say `https://cassini.local/`, which tells you how far along the ecosystem story
is.

The specification is also written for meetings, and only meetings. The same
mechanism (audio + timestamped text + provenance) would cover lectures, songs
with synced lyrics, podcasts with chapters, audiobooks. Making it cover them is
not done.

Two open questions I have no answer to yet, both spelled out in
[`design/research-brief-2026-03-17.md`](design/research-brief-2026-03-17.md):

* Should this build on an existing standard rather than invent tags? WebVTT,
  TTML, SYLT in ID3, Podcasting 2.0, TextGrid and RTTM all overlap with parts of
  what we do. I did not do that survey properly before writing v1. I might be
  reinventing something with a worse name.
* Should it stay Ogg Opus only, or become container-agnostic with per-container
  profiles? Ogg comment tags have a practical capacity ceiling we haven't hit
  but can see from here, and FLAC or M4A would suit some of the other use cases
  better.

There is also one thing we lose today and want back: when several participant
tracks get mixed into one, the map of which time range came from which source
is discarded. Keeping it would help anyone who wants to re-diarize the audio
later.

## contributing

Issues and PRs welcome, especially on the two open questions above. If you have
built something that reads or writes these files, I'd like to hear about it,
because right now the answer to "who else implements this" is nobody.

Licensed [AGPL-3.0](LICENSE), same as gocassini.
