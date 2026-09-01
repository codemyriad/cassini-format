# cassini-format

A Cassini portable meeting is an ordinary `.opus` file. Double-click it and any
audio player plays it, because that is all it is: Ogg Opus, 48 kHz. But it also
carries the full word-timestamped transcript, the speakers, and a record of
which models produced what, embedded in the OpusTags where players that don't
care will simply ignore them.

The best plain-language description of it is
[`design/public-page-draft-2026-08-28.md`](design/public-page-draft-2026-08-28.md),
drafted as the format's future public page. Start there if you want to know what
the format *is*. [`SPEC.md`](SPEC.md) is what it currently *does*, which is not
the same thing yet.

This repository is the specification, the schemas and the open decisions. The
implementation lives in [gocassini](https://github.com/codemyriad/gocassini),
which records, transcribes and packs these files. The two were the same repo
until now; I split the format out because a format that only one program can
read isn't really a format.

Try it on a file:

```bash
tools/cassini-extract.py meeting.opus --tags     # the descriptor tags
tools/cassini-extract.py meeting.opus --list     # which transcripts are inside
tools/cassini-extract.py meeting.opus            # the whole manifest as JSON
```

That script is about 180 lines of Python and it shells out to `ffprobe`. It
doesn't import anything Cassini-specific, on purpose: if the format is really
self-describing, a reader should be writable from the tags alone. Consider it
both a tool and a conformance check.

## what's here

* [`SPEC.md`](SPEC.md) — the format as shipped, v1 through v3, with the
  rationale and the rejected alternatives kept in place
* [`spec/`](spec/) — the JSON Schemas for the manifest (v1, v2, v3), plus
  [`cassini-opus-audio-integrity-v1.md`](spec/cassini-opus-audio-integrity-v1.md),
  the byte-level definition of the audio digest
* [`design/format-freeze-2026-08-28.md`](design/format-freeze-2026-08-28.md) —
  **read this before implementing anything.** Ten changes wanted before the
  format is published, most of them still outstanding
* [`design/naming.md`](design/naming.md) — the wire name is not decided
* [`design/`](design/) — also the multi-transcript proposal that became v2, the
  2026-03 research brief, and the operator's sealing rules
* [`tools/`](tools/) — the reference extractor
* [`LICENSE.md`](LICENSE.md) — CC-BY-4.0 prose, CC0 schemas and tools

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
* **The digest binds the transcript to the recording.** Not a seal, and not
  proof of authenticity: anyone who rewrites the transcript can recompute every
  hash. It answers one question, "is this transcript describing this
  recording?", and it catches accidents rather than adversaries.

That last one is where v3 differs from v1 and v2. v1 hashed decoded PCM, which
meant a consumer had to decode the entire file to check identity, and it turned
out not even to be stable: the two Opus decoders inside one ffmpeg binary
produce different PCM for the same file, so meeting identity depended on which
decoder you linked. v3 hashes the compressed Opus packets instead, with a
canonical byte stream defined in
[`spec/cassini-opus-audio-integrity-v1.md`](spec/cassini-opus-audio-integrity-v1.md).
It deliberately excludes `OpusTags`, because otherwise writing the digest into
the file would change the digest. v2, in between, is what let one file hold
several transcripts of the same audio (parakeet next to canary, raw next to
human-corrected) without duplicating the recording.

## status: pre-freeze, and that is the whole point

Publishing freezes a format. Every tag name and schema field becomes someone
else's compatibility problem the moment a third party implements it. So this is
the last chance to fix things, and a review on 2026-08-28 found ten of them.
[`design/format-freeze-2026-08-28.md`](design/format-freeze-2026-08-28.md) has
all of it. The three I would not publish without:

* **The integrity rules are wrong about the lifecycle.** They were written to
  catch edited audio. In practice the audio never changes and the transcript
  does, because reprocessing with a fixed Cassini is the normal life of a file.
  Rule 3 makes discarding the transcript a MUST on any mismatch, and it was
  firing on every shipped file over a 312-sample pre-skip. A reader should keep
  the transcript and label it unverified.
* **The schemas can't grow.** `additionalProperties: false` appears 13 times in
  the v3 schema and nothing says what a reader does with a member it doesn't
  recognise, so any field nobody has thought of yet is a major version bump.
* **`cassini.words.v1` is defined nowhere.** The transcript body format, the
  actual payload, the thing an implementer most needs, exists in the repo only
  as a string value, and the Go producer and the JS viewer disagree about the
  shape it names. That schema has to be written before any of this ships.

The wire name is also unsettled: `CASSINI_` everywhere, `cairn/2` in the public
page draft, and a real argument for just keeping CASSINI. See
[`design/naming.md`](design/naming.md). Nothing has been renamed in a file yet,
and until that decision lands nothing should be.

One thing we lose today and want back: when several participant tracks get mixed
into one, the map of which time range came from which source is discarded.
Keeping it would help anyone who wants to re-diarize the audio later. That is
what the open `payloads[]` in freeze item 3 is for.

And two questions from the [2026-03 research
brief](design/research-brief-2026-03-17.md) that nobody has answered:

* Should this build on an existing standard rather than invent tags? WebVTT,
  TTML, SYLT in ID3, Podcasting 2.0, TextGrid and RTTM all overlap with parts of
  what we do. I did not do that survey properly before writing v1. I might be
  reinventing something with a worse name.
* Should it stay Ogg Opus only, or become container-agnostic with per-container
  profiles? FLAC or M4A would suit some other use cases (lectures, songs with
  synced lyrics, audiobooks) better.

## contributing

Issues and PRs welcome, especially on the freeze list and the two open questions
above. If you have built something that reads or writes these files, I'd like to
hear about it, because right now the answer to "who else implements this" is
nobody.
