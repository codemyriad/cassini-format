# Cassini portable meeting format

Date: 2026-09-02

Status: published, version 1

A Cassini portable meeting is an ordinary Ogg Opus file that also carries its
own transcript. Who spoke, what they said word by word with timestamps, and what
produced that text all live in the file's OpusTags comment header, next to
`TITLE` and `DATE`. A player that knows none of this plays the audio and ignores
the rest.

The metadata has two layers. The first is plain comments any tool can show. The
second is a JSON manifest, gzipped, base64url-encoded and split across numbered
comments so the header stays inspectable. Each transcript body is a second such
payload under its own prefix. A SHA-256 over the Opus packets ties the transcript
to the recording.

This is what a file looks like to `ffprobe`, with the payload chunks elided:

```text
TITLE=Lantern Festival Booth Run-through
DATE=2026-04-15T09:12:00Z
CASSINI_FORMAT=org.cassini.portable-meeting/1
CASSINI_PROFILE=ogg-opus
CASSINI_PAYLOAD_ENCODING=base64url+gzip+utf8json
CASSINI_PAYLOAD_CHUNK_COUNT=1
CASSINI_PAYLOAD_SHA256=a4d048386f81bd4b2814…
CASSINI_PAYLOAD_000=H4sIAAAAAAAC_61W227jNhD9lYFe2mIt…
CASSINI_TRANSCRIPT_IDS=script
CASSINI_TRANSCRIPT_DEFAULT=script
CASSINI_TX_SCRIPT_PAYLOAD_CHUNK_COUNT=3
CASSINI_TX_SCRIPT_PAYLOAD_SHA256=bcfe6a717171545ef264…
CASSINI_TX_SCRIPT_PAYLOAD_000=H4sIAAAAAAAC_…
CASSINI_AUDIO_OPUS_SHA256=8e1f7499c6d5fba88c3b…
CASSINI_MEETING_ID=mtg_8e1f7499c6d5fba8…
CASSINI_SPEAKER_COUNT=6
CASSINI_DECODE_HINT=Concatenate CASSINI_PAYLOAD_000..N for the manifest; …
```

The words MUST, SHOULD and MAY are used as in RFC 2119. Everything else is
explanation.

> [`ERRATA.md`](ERRATA.md) lists where the reference implementation does not yet
> do what this document says. Read it before implementing.

<!-- spec:part v1 -->

## Implementing this

Read these in order. Each settles something the next assumes.

1. This document: the tags, the chunk transport, the manifest, and what a
   consumer does in each state it can end in.
2. [`spec/cassini-portable-meeting-manifest-v1.schema.json`](spec/cassini-portable-meeting-manifest-v1.schema.json):
   the manifest. The schema is normative for the structure it expresses; this
   prose is normative for everything the schema cannot say, such as rules that
   span two members. A contradiction between them is a bug in this repository,
   not a rule; report it.
3. [`spec/cassini-words-v1.md`](spec/cassini-words-v1.md): the transcript body,
   which is what a `CASSINI_TX_<ID>_PAYLOAD_` chunk set decodes to.
4. [`spec/cassini-opus-audio-integrity-v1.md`](spec/cassini-opus-audio-integrity-v1.md):
   the byte stream behind `CASSINI_AUDIO_OPUS_SHA256`. Needed only to compute or
   verify the audio digest.

### What this format inherits

Everything about the container, the codec and the comment header comes from
existing specifications. This document does not restate them.

| Need | Defined in |
|---|---|
| Ogg page layout, header flags, lacing and packet reassembly | RFC 3533 §5, §6 |
| `OpusHead` alone on the first page; `OpusTags` is the second packet and MAY span pages; audio starts on a fresh page | RFC 7845 §3 |
| `OpusHead` fields, including pre-skip at bytes 10–11 | RFC 7845 §5.1 |
| `OpusTags` layout: magic, vendor string, comment count, length-prefixed comments | RFC 7845 §5.2 |
| A comment is UTF-8 `NAME=value`; names are case-insensitive ASCII; the first `=` separates; a name MAY repeat | Vorbis comment spec, RFC 7845 §5.2.1 |
| Opus packet duration from the TOC byte; a packet is at most 120 ms | RFC 6716 §3.1, §3.2.5 |
| base64url, the URL-safe alphabet | RFC 4648 §5 |
| gzip | RFC 1952 |

One thing upstream leaves incomplete: the Ogg page CRC. RFC 3533 gives the
polynomial and stops. The full parameters are in
[`spec/cassini-opus-audio-integrity-v1.md`](spec/cassini-opus-audio-integrity-v1.md),
because that is where a consumer needs them.

## The file

### File identification

A file is a Cassini portable meeting when all three hold:

1. it is Ogg Opus;
2. its comment vector carries `CASSINI_FORMAT`;
3. its comment vector carries a complete payload descriptor.

The **payload descriptor** is the smallest set of tags that says both "this is
a Cassini file" and "here is how to decode it". It is exactly these four:

| Tag | Value |
|---|---|
| `CASSINI_FORMAT` | `org.cassini.portable-meeting/1` |
| `CASSINI_PAYLOAD_ENCODING` | `base64url+gzip+utf8json` |
| `CASSINI_PAYLOAD_CHUNK_COUNT` | a decimal integer, 1 or more |
| `CASSINI_PAYLOAD_000` … `CASSINI_PAYLOAD_<COUNT-1>` | every index present, none empty |

Everything else a producer MUST write (below) is checked after identification,
not as part of it.

What a consumer does with the answer:

| Finding | State |
|---|---|
| no `CASSINI_FORMAT` | `plain-audio`. Play it. Not an error. |
| `CASSINI_FORMAT` names a major version this consumer does not implement | `unknown-cassini-format`. Play it. |
| `CASSINI_FORMAT` present, descriptor incomplete | `invalid-cassini-metadata`. Play it. |

The states are defined under [Trust and integrity](#trust-and-integrity).

This document defines one version, `org.cassini.portable-meeting/1`. Two
shapes came before it. Both were used only inside Cassini, neither was ever
published, and they are kept in [`spec/drafts/`](spec/drafts/) for anyone who
has to read one of those private files. Nothing in this document is
version-conditional.

### Audio

| | |
|---|---|
| Container | Ogg (MUST) |
| Codec | Opus (MUST) |
| Sample rate field | `48000` (MUST) |
| Channels | mono for speech; stereo only when the stereo content is deliberate (SHOULD) |
| Program | one continuous playable stream (SHOULD) |

### Extensibility

The format grows without a version bump. The rule for anything a consumer does
not recognise is: ignore it and carry on.

- A consumer MUST ignore an unrecognised tag, and an unrecognised manifest
  member at any depth. Neither is an error.
- A tool that rewrites tags or the manifest MUST carry unrecognised ones forward
  unchanged. Dropping what you did not understand is how a format loses data
  another tool put there on purpose.
- Ignoring the unknown does not loosen the known. `version` is still an
  integer; `kind` is still the fixed string.

Two objects are closed: `integrity`, and every `payloadRef`. Every member of
those is an instruction for reassembling bytes or deciding whether audio and
transcript belong together, so an unrecognised member there is not a lost
hint. Adding a member to either is a new major version, and the schemas reject
one. A consumer that meets one in `integrity` cannot know what a match would
mean and reports [`unverified`](#unverified); in a `payloadRef` it treats that
transcript as unavailable.

**Private use.** Tag names beginning `X_` and the manifest member `x` are
reserved for private data and will never be defined here.

- A private tag SHOULD be `X_<OWNER>_<NAME>`, where `<OWNER>` is a domain the
  producer controls, upper-cased, with anything outside `A–Z0–9` replaced by
  `_`: `X_EXAMPLE_COM_TICKET=OPS-14`.
- The manifest member `x` is an object keyed by that domain:
  `"x": {"example.com": {"ticket": "OPS-14"}}`. Private data goes under `x`
  and nowhere else. A tool publishing a recording outside the organisation
  strips private data by deleting `x` and every `X_*` tag.
- Consumers MUST ignore private data they do not own. A tool that edits `x`
  MUST recompute `CASSINI_PAYLOAD_SHA256` and `CASSINI_PAYLOAD_RAW_BYTES`.

**Reserved.** The manifest member `payloads` and the tag prefix `CASSINI_PL_`
are held for a later revision. Producers MUST NOT write them; consumers MUST
ignore them.

## Tags

### Reading the comment vector

The tags are Vorbis comments in the `OpusTags` packet: the second packet of the
stream, which MAY span several pages. A consumer MUST reassemble the whole
packet before parsing it. Taking "the second page" instead of "the second
packet" truncates any header longer than one page, which is most of them.

A consumer MUST read every comment. RFC 7845 lets a generic Opus reader ignore
comments past the first 61,440 octets; a Cassini reader MUST NOT, because on a
long recording the tags that make the file decodable can sit past that mark.
It MUST still bound its own allocation, and MAY reject a header over 120 MB.

A consumer fetching over HTTP MAY request only a prefix of the file, since the
header is at the front. If the range does not contain a complete `OpusTags`
packet, it MUST fetch more rather than parse what it has.

Three things the Vorbis comment format leaves open, pinned down here:

- **The separator is the first `=`.** A value MAY contain more of them.
- **Names are case-insensitive.** Producers MUST write `CASSINI_*` names in
  upper case. Consumers MUST fold ASCII case on the name before comparing, and
  MUST compare the value exactly as written. A tool rewriting a tag on a file it
  did not write MUST replace the spelling already there, not add a second
  comment under the canonical one.
- **A name MAY repeat, and Cassini never repeats one.** Producers MUST NOT
  write a `CASSINI_*` name twice. A consumer that sees a repeat of a
  load-bearing tag MUST report `invalid-cassini-metadata` rather than pick one.
  Load-bearing means `CASSINI_FORMAT` and every `CASSINI_PAYLOAD_*` and
  `CASSINI_TX_*` tag. For any other `CASSINI_*` tag it SHOULD use the
  manifest's value and report the repeat.

`ENCODER` and the vendor string belong to the muxer, not the producer. ffmpeg
writes `encoder=Lavf<version>` whatever it was asked for.

### Cassini descriptor tags

Every tag below is REQUIRED, and every one MUST carry a non-empty value. A
producer with no value for one of them has a file it cannot write.

**Identity**

| Tag | Value |
|---|---|
| `CASSINI_FORMAT` | `org.cassini.portable-meeting/1` |
| `CASSINI_PROFILE` | `ogg-opus` |

**The manifest chunk set**

| Tag | Value |
|---|---|
| `CASSINI_PAYLOAD_MIME` | `application/vnd.cassini.portable-meeting+json` |
| `CASSINI_PAYLOAD_ENCODING` | `base64url+gzip+utf8json` |
| `CASSINI_PAYLOAD_SCHEMA` | `https://cassini-format.codemyriad.io/schema/cassini-portable-meeting-manifest-v1.schema.json` |
| `CASSINI_PAYLOAD_CHUNK_COUNT` | decimal integer, 1 or more |
| `CASSINI_PAYLOAD_SHA256` | lowercase hex SHA-256 of the decompressed JSON bytes |
| `CASSINI_PAYLOAD_RAW_BYTES` | decimal, the decompressed length |
| `CASSINI_PAYLOAD_GZIP_BYTES` | decimal, the compressed length |
| `CASSINI_PAYLOAD_000` … | the chunks; see [Chunk sets](#chunk-sets) |

**The transcript index**

| Tag | Value |
|---|---|
| `CASSINI_TRANSCRIPT_IDS` | the ids in `transcripts[]`, comma-separated, no spaces, sorted |
| `CASSINI_TRANSCRIPT_DEFAULT` | the id a viewer opens first |
| `CASSINI_TX_<UPPER_ID>_PAYLOAD_*` | one chunk set per transcript; see [Transcripts and their chunk sets](#transcripts-and-their-chunk-sets) |

`CASSINI_TRANSCRIPT_IDS` is sorted; `transcripts[]` is in producer order. A
consumer MUST compare them as sets.

**Audio shape and identity**

| Tag | Value |
|---|---|
| `CASSINI_AUDIO_SAMPLE_RATE` | `48000`. A constant: Opus always decodes at 48 kHz. |
| `CASSINI_AUDIO_CHANNELS` | `1` or `2` |
| `CASSINI_AUDIO_SAMPLE_COUNT` | playable samples at 48 kHz, as defined by the digest spec |
| `CASSINI_AUDIO_DURATION_MS` | `sampleCount * 1000 / 48000`, integer division, truncated |
| `CASSINI_AUDIO_MATCH_POLICY` | `exact-opus-audio-v1` |
| `CASSINI_AUDIO_OPUS_SHA256` | lowercase hex SHA-256 of the canonical Opus packet stream |

**For a reader who has none of this document**

| Tag | Value |
|---|---|
| `CASSINI_DECODE_HINT` | `Concatenate CASSINI_PAYLOAD_000..N for the manifest; for a transcript body concatenate CASSINI_TX_<ID>_PAYLOAD_000..N. Each chunk set: base64url decode, gzip decompress, parse UTF-8 JSON.` |

### Summary and mirror tags

Three summary tags let a reader show something before decoding anything.
Producers SHOULD write them; consumers MUST NOT require them.

| Tag | Value |
|---|---|
| `CASSINI_MEETING_ID` | the manifest's `meeting.id` |
| `CASSINI_CREATED_AT` | RFC 3339 UTC |
| `CASSINI_SPEAKER_COUNT` | decimal |

Four optional tags mirror the origin fields of `meeting`. Each is written only
when its value is known: absent, never empty.

| Tag | Mirrors |
|---|---|
| `CASSINI_ROOM_ID` | `meeting.roomId` |
| `CASSINI_ROOM_NAME` | `meeting.roomName` (no longer written; still read) |
| `CASSINI_JOB_ID` | `meeting.jobId` |
| `CASSINI_ATTEMPT_NUMBER` | `meeting.attemptNumber` |
| `CASSINI_PROCESSED_AT` | `meeting.processedAtUtc` |
| `CASSINI_RECORDED_AT_LOCAL` | `meeting.recordedAtLocal` |

Producers SHOULD also write `TITLE`, `DATE` and a one-line `DESCRIPTION` saying
how to decode the payload, so that ordinary tools show something useful.

All of these are copies. The manifest is the record; see
[When a tag and the manifest disagree](#when-a-tag-and-the-manifest-disagree).

### Comment order

Nothing in this format depends on the order comments appear in. Chunks are
reassembled by the index in their name, never by position.

RFC 7845 lets a generic reader ignore comments past the first 61,440 octets of
the header, and a long recording's payload passes that mark. In practice
nothing truncates: `ffmpeg -c copy`, a remux and a tag-library round-trip all
preserve every comment on a 300 KB header, and these files are played, not
edited. The format accepts the exposure.

A producer MAY write `CASSINI_FORMAT` first, then every other non-chunk tag,
then the numbered chunks. That keeps everything load-bearing inside the window
at no cost. Sorting the whole list does the opposite, because `CASSINI_PAYLOAD_000`
sorts before `CASSINI_PAYLOAD_CHUNK_COUNT`.

## Chunk sets

A **chunk set** carries a document of any size in Vorbis comments. It is a
prefix `P` and seven kinds of tag:

| Tag | Holds |
|---|---|
| `P` `MIME` | the media type of the decoded document |
| `P` `ENCODING` | how to turn the concatenated text back into bytes |
| `P` `CHUNK_COUNT` | how many numbered tags follow |
| `P` `SHA256` | lowercase hex SHA-256 of the decoded bytes |
| `P` `RAW_BYTES` | the decoded length |
| `P` `GZIP_BYTES` | the compressed length |
| `P` `000` … `P` `<N-1>` | the document |

A file carries at least two: the manifest, whose prefix is `CASSINI_PAYLOAD_`,
and one per transcript, whose prefix is that entry's `payloadRef.prefix`.

Rules, the same for every chunk set:

- Indexing starts at `000`. The index is decimal, zero-padded to at least three
  digits, and grows past three when it must: `999`, `1000`. Consumers MUST
  parse it as a number.
- Every index from `000` to `CHUNK_COUNT-1` MUST be present. A consumer MUST
  reassemble by generating those names and looking each up. A missing index
  makes the set unreadable; a consumer MUST NOT concatenate across a gap.
- A chunk name MUST appear once. A consumer that sees a repeat MUST treat the
  set as unreadable.
- Chunk tags numbered past `CHUNK_COUNT-1` are ignored, but a repeat among
  them is still a repeat. A tool replacing a chunk set MUST delete every
  numbered tag under that prefix first; a stale chunk is old text left in a
  file that was meant to lose it.
- Values are concatenated in numeric index order with no separator, then
  decoded once. A single chunk is not decodable on its own.
- Producers SHOULD keep each chunk to 4096 characters. Nothing depends on it;
  it keeps the header readable in tools that print one tag per line.
- A chunk tag is the prefix followed by digits only. `CASSINI_PAYLOAD_SCHEMA`
  starts with the manifest's prefix and is not a chunk. A tool that matches the
  prefix alone deletes required descriptors.

**Which declaration wins.** For the manifest, the `CASSINI_PAYLOAD_*` tags are
the record, because there is no manifest yet. For a transcript body, the
entry's `payloadRef` is the record for all seven values, and the matching
`CASSINI_TX_*` tags are a copy. A disagreement there is a warning, not a
failure.

### Payload encoding

The one encoding defined is `base64url+gzip+utf8json`:

1. compact UTF-8 JSON: no insignificant whitespace, no trailing newline, no
   byte-order mark. The set's `SHA256` is over exactly these bytes.
2. gzip, RFC 1952.
3. base64url, RFC 4648 §5, **unpadded**, no line breaks.
4. split across the numbered tags.

Producers MUST write unpadded. Consumers MUST accept both padded and unpadded,
and MUST strip ASCII whitespace (space, tab, CR, LF) before deciding how much
padding to add: a comment value may legally contain a newline.

Strictness, so that two readers agree on what is damaged:

- A decimal tag value is `0|[1-9][0-9]*`, at most 2^53−1. Anything else is
  malformed.
- base64url is strict: a byte outside the alphabet, padding anywhere but the
  end, or non-zero trailing bits is a decode failure (RFC 4648 §3.5).
- One gzip member, nothing after it.
- UTF-8 decoding is fatal on an invalid sequence. A JSON object with a
  repeated member name is malformed.

`RAW_BYTES` is a bound, not decoration. A gzip stream can claim to be small and
inflate to gigabytes. Consumers MUST stop inflating once the output exceeds the
declared `RAW_BYTES` and treat the result as damaged. The declared value is
untrusted: a consumer MUST also apply a ceiling of its own, and MUST bound the
comment count, chunk count and JSON depth it will accept. Producers SHOULD keep
every chunk set under 64 MiB decompressed; a consumer MAY reject one above
that.

A consumer MUST check the declared `SHA256` before believing any field of the
result. For the manifest, an absent digest is a missing required tag and the
file is `invalid-cassini-metadata`. For a body, it makes that transcript
unavailable.

A consumer MUST NOT decode a chunk set whose `ENCODING` it does not implement.
For the manifest that is `invalid-cassini-metadata`; for a body, that
transcript is unavailable.

## The manifest

### Embedded manifest

The decoded `CASSINI_PAYLOAD_` chunk set is one JSON object. Its schema is
[`spec/cassini-portable-meeting-manifest-v1.schema.json`](spec/cassini-portable-meeting-manifest-v1.schema.json).

Three members identify the document:

| Member | Value |
|---|---|
| `kind` | `cassini-portable-meeting`. Any other value: not a portable meeting. |
| `version` | `1`. MUST match `CASSINI_FORMAT`; a disagreement is `invalid-cassini-metadata`. |
| `profile` | `ogg-opus`. Any other value: not a portable meeting. |

Required alongside them: `meeting`, `audio`, `integrity`, `speakers`,
`transcripts`. Optional: `readableTranscripts`, `provenance`, `chapters`,
`summary`, `attachments`, `x`.

The manifest is an index. It does not contain the transcript; it points at it.
A consumer that wants only the title, date and speaker list never decodes a
transcript body.

### `meeting`

Required:

- `id`: a stable identifier. The reference producer writes `mtg_` plus the 64
  hex characters of `integrity.opusAudioSha256`, so a tag rewrite keeps the id
  and a re-encode changes it. Any producer MAY use any stable non-empty string.
  Consumers MUST NOT parse it.
- `title`: non-empty.
- `createdAtUtc`: RFC 3339 UTC. When the pipeline stamped this artifact, which
  is not when the meeting happened.
- `durationMs`: playable duration.

Optional:

- `recordedAtLocal`: wall-clock time at the recording site,
  `YYYY-MM-DDTHH:MM:SS`, no offset and no zone. It is a label, not an
  instant: consumers MUST NOT convert it to one.
- `processedAtUtc`: RFC 3339 UTC.
- `summary`: a short plain-text summary of the meeting, for display.
- `language`: BCP-47. The reference producer never writes it.
- `roomId`: a one-way derivation of the room's identity, `rm_<16 lowercase
  hex>`. Never the identity itself: a Nextcloud Talk conversation token is also
  the link that joins the conversation, and this file travels. Producers MUST
  NOT write a raw room token in any tag or manifest member.
- `roomName`: no longer written, still read. A display name is editable and a
  published recording is not.
- `jobId`, `attemptNumber`: the producer job, and which attempt, 1-based. A
  consumer MUST treat a non-positive `attemptNumber` as absent.

### `audio`

What is actually stored. All six required: `container` (`ogg`), `codec`
(`opus`), `sampleRate` (`48000`), `channels` (`1` or `2`), `sampleCount`,
`durationMs`.

### `integrity`

Whether this manifest still describes the audio in this file. All six
required:

- `matchPolicy`: `exact-opus-audio-v1`.
- `opusAudioSha256`: 64 lowercase hex, over the stream defined in
  [`spec/cassini-opus-audio-integrity-v1.md`](spec/cassini-opus-audio-integrity-v1.md).
- `sampleRate`, `channels`, `sampleCount`, `durationMs`: MUST equal their
  counterparts in `audio`.

What a consumer does with the answer is under
[Trust and integrity](#trust-and-integrity).

### `speakers`

The table transcript items point at. Each entry has a non-empty `id` and a
`label`, the name a reader displays. The array MAY be empty. Producers MUST
write an entry for every speaker their transcripts name. An item whose
`speaker` matches nothing is still transcript content; render it under an
unknown speaker rather than dropping it.

### `transcripts`

The index of word-timed transcripts, at least one entry. Each entry names the
chunk set that carries its body. These are the canonical transcript; anything
derived from them is optional and regenerable.

`readableTranscripts` is the optional index of derived transcripts. Each entry
MUST name its source in `sourceTranscriptId`, and that id MUST be one of the
transcripts this file declares.

### `provenance`

Optional. Which systems produced each layer, so a user can see what made the
file.

- `speechToText`, `readableCleanup`, `displayTranscript`: maps keyed by
  transcript id. A transcript with `id: "canary"` resolves to
  `provenance.speechToText.canary`.
- `meetingSummary`: one processing step.
- `attribution`: how speaker attribution ran. Required `ran`, `mode`,
  `wordsMeasured`, `wordsFlagged`, `wordsDropped`; optional `reason`,
  `thresholdDb`. `mode` is an open string.
- `wordTimings`: `{ "endsBoundedByAudio": true }`. A consumer keys off its
  presence, not its value. Absent means word ends are unvouched for and may run
  past silence; a repair that clips them is right on such a file and wrong on
  one that carries the record.

A processing step has only optional strings: `backend`, `engine`, `model`,
`device`, `language`, `source`, `version`. Producers MUST NOT put a URL or a
hostname in any of them. This file is cleartext to everyone who receives it.

### `chapters`, `summary`, `attachments`

All optional. `chapters` entries carry `startMs`, `endMs`, `title`.

An attachment is `{ "name", "mime", "contentBase64" }`: a file name unique
within the array, its media type, and its bytes in **standard base64, not
base64url**, the one place the alphabet differs. A consumer MUST ignore an
entry it cannot decode. `summary` is metadata about a summary (the reference
producer writes `format`, `model`, `backend`); the summary itself is the
attachment named `summary.md`. Attachments are for small things: they sit
inside the manifest chunk set and count against its bound.

### Transcripts and their chunk sets

Each entry in `transcripts[]` and `readableTranscripts[]`:

```jsonc
{
  "id":      "canary",            // ^[a-z0-9][a-z0-9-]{0,31}$, unique in file
  "role":    "raw-asr",
  "default": true,                // at most one per slot
  "format":  "cassini.words.v1",
  "language": "en",
  "wordCount": 9224,
  "createdAtUtc": "2026-05-12T14:40:00Z",
  "payloadRef": {
    "prefix":     "CASSINI_TX_CANARY_PAYLOAD_",
    "chunkCount": 14,
    "sha256":     "…",            // of the decompressed body
    "rawBytes":   718432,
    "gzipBytes":  221110,
    "mime":       "application/vnd.cassini.transcript-words+json",
    "encoding":   "base64url+gzip+utf8json"
  }
}
```

`role` says how the text came to exist:

| Role | What it is | `sourceTranscriptId` |
|---|---|---|
| `raw-asr` | what a recogniser produced from the audio | MUST NOT carry one |
| `human-corrected` | that text after a person fixed it | required |
| `translation` | it in another language | required |
| `scripted` | authored text the recording was made *from* | MUST NOT carry one |
| `readable-cleanup`, `display` | derived views, in `readableTranscripts[]` only | required |

`scripted` is the odd one. Some recordings are performances of words that
already existed: a song's lyrics, a read script. That text is not a
transcription; it is what the audio is a performance of, so it is authoritative
rather than derived. A producer that writes both SHOULD flag the `scripted`
entry as the default. One is the words; the other is a guess at them. The
consumer's resolution rule below does not change.

The body of every entry is
[`spec/cassini-words-v1.md`](spec/cassini-words-v1.md). The media type is
`application/vnd.cassini.transcript-words+json` for a word-timed body and
`application/vnd.cassini.transcript-readable+json` for a derived one.

**The chunk set.** `payloadRef.prefix` is authoritative; a consumer MUST use it
as written and MUST NOT re-derive it. A producer derives it as `CASSINI_TX_` +
the id upper-cased with `-` replaced by `_` + `_PAYLOAD_`. Beside the chunks, the
six descriptors `_MIME`, `_ENCODING`, `_CHUNK_COUNT`, `_SHA256`, `_RAW_BYTES`,
`_GZIP_BYTES` are REQUIRED under that prefix, and each is a copy of the
`payloadRef` member of the same name.

### Reserved transcript ids

An id MUST match `^[a-z0-9][a-z0-9-]{0,31}$` and MUST be unique in the file.

`-` is legal and `_` is not, because the tag prefix replaces `-` with `_`:
`raw-asr` and `raw_asr` would share one chunk set and one body would be lost
without an error. Producers MUST reject an id containing `_`, and MUST reject
two ids whose prefixes collide.

These ten are reserved. They are the manifest's own top-level names, held back
so an id can never read as one in a log line or a tag dump:

```text
payload, format, audio, meeting, integrity, transcript,
provenance, summary, attachments, speakers
```

### Audio integrity

The digest covers the playback-relevant `OpusHead` fields, every audio packet
in order with its length, and the playable sample count. It excludes `OpusTags`
and all Ogg framing. That is what makes it non-circular: the manifest can carry
its own audio digest, and rewriting the tags cannot change it.

Producers MUST compute it without decoding the audio, and MUST verify it against
the file they are about to publish, not the input they encoded. The byte-level
rule is [`spec/cassini-opus-audio-integrity-v1.md`](spec/cassini-opus-audio-integrity-v1.md).

## Reading a file

The read path, in order. A consumer that performs these steps reads every file
this format defines.

1. **Find the tags.** Reassemble `OpusTags` and parse the comment vector.
   [Reading the comment vector](#reading-the-comment-vector).
2. **Decide what the file is.** [File identification](#file-identification).
3. **Reassemble the manifest.** The `CASSINI_PAYLOAD_` chunk set.
   [Chunk sets](#chunk-sets).
4. **Decode and verify it.** Bound the inflate, then check the digest and byte
   counts. [Payload encoding](#payload-encoding).
5. **Read the manifest.** Check `kind`, `version` and `profile`. Ignore what
   you do not recognise. [Embedded manifest](#embedded-manifest).
6. **Resolve which transcript to show.** Next section.
7. **Decode its body.** Its chunk set, by steps 3 and 4, with `payloadRef` as
   the record. The body is [`spec/cassini-words-v1.md`](spec/cassini-words-v1.md).
8. **Decide whether to trust it, and say so.**
   [Trust and integrity](#trust-and-integrity).

In every state, a consumer MUST keep playing the audio. A file that played
before a Cassini reader touched it MUST play afterwards. Consumers SHOULD show
title, date and speaker count before rendering a transcript, since those are
one small chunk set away and a body may be many.

### Resolving a transcript

There are three slots. A consumer fills each from the entries of one array
with one set of roles:

| Slot | Array | Roles | Body `format` |
|---|---|---|---|
| words | `transcripts[]` | `raw-asr`, `human-corrected`, `translation`, `scripted` | `cassini.words.v1` |
| readable | `readableTranscripts[]` | `readable-cleanup` | as the entry says |
| display | `readableTranscripts[]` | `display` | as the entry says |

For each slot, in this order:

1. the first entry whose `default` is `true`;
2. failing that, the first entry.

Array order is therefore normative. Zero flagged defaults is a legal file.
`CASSINI_TRANSCRIPT_DEFAULT` is the id this rule selects for the words slot.

When showing a readable transcript beside the words, a consumer SHOULD prefer
the entry whose `sourceTranscriptId` names the words it is showing.

`CASSINI_TRANSCRIPT_IDS` and `CASSINI_TRANSCRIPT_DEFAULT` are copies. A consumer
MUST ignore an id in the tag that is not in the manifest, and MUST ignore a
default that names no entry. Where tag and flag both resolve and disagree, the
manifest wins.

Beside the file's trust state, each selected transcript is **available** or
**unavailable**. A body whose chunk set is missing a chunk, whose count, byte
counts or digest disagree, or whose decode fails is unavailable, and the file's
state is unaffected: the state describes the manifest and the audio. The other
transcripts, the speakers and the meeting are still good. The consumer MUST say
which transcript it could not load, and `ok` with no transcript on screen is a
legal outcome. A repeated tag is different: it is evidence the file was edited,
and [the comment-vector rule](#reading-the-comment-vector) applies.

### Trust and integrity

`integrity` answers one question: do this transcript and this audio belong
together? It is a **join key, not a seal**. It is not evidence that the audio
is authentic or the transcript accurate, and anyone who rewrites the transcript
can recompute every digest.

Nothing below throws a transcript away. The audio of a real file does not
change and the transcript does, because reprocessing with a better model is the
normal life of a meeting. A reader that discards the transcript on a failed
check is wrong far more often than right. The hard check belongs in the
producer, which can refuse to ship. The consumer has a user in front of it.

A consumer MUST end every read in exactly one of these states and MUST make it
visible to whoever called it. The names are normative.

| State | Meaning | The consumer |
|---|---|---|
| `plain-audio` | no `CASSINI_FORMAT` | plays it; not an error |
| `unknown-cassini-format` | a major version it does not implement | plays it; MAY show `meeting`, `audio`, `speakers`; MUST NOT present a transcript it does not understand |
| `invalid-cassini-metadata` | present, cannot be reconstructed | plays it; says which step failed; MUST NOT render a partial manifest |
| `unverified` | readable, audio not checked | opens it; shows the transcript; marks it unverified wherever shown |
| `stale-audio` | readable, checked, does not match | opens it; keeps and shows the transcript; labels it; names the failed check |
| `ok` | readable, checked, matches | opens it |

Test them in table order; the first that applies is the state.

#### `plain-audio`

`CASSINI_FORMAT` is absent. The ordinary case for an ordinary `.opus`.

#### `unknown-cassini-format`

The Opus stream is valid whatever the metadata says. The consumer SHOULD say
the file carries metadata in a version it cannot read.

#### `invalid-cassini-metadata`

The manifest cannot be trusted at all. A required `CASSINI_PAYLOAD_*` tag is
missing or malformed; a load-bearing tag is repeated; a manifest chunk is
missing; the count, byte counts or digest disagree; the decode, the UTF-8 or
the JSON fails; `kind` or `profile` is wrong; `version` disagrees with
`CASSINI_FORMAT`; a required member is missing or of the wrong type. A
malformed optional member is not on this list: it is ignored as if absent.
The consumer MUST NOT show any manifest field.

#### `unverified`

The consumer did not check the audio, or could not. It has not read the audio
bytes (a byte-range fetch, a tag tool); the file carries no digest; the digest
in the manifest and the one in the tags disagree, so there is no single claim
to check; the digest parser rejected the stream (a page CRC failure, a sequence
gap, a chained or multiplexed stream, a missing end-of-stream flag); or
`integrity` carries a member this consumer does not recognise, so it cannot
know what a match would mean. In each case the consumer SHOULD say why.

A consumer that never verifies audio is conforming, and MUST report `unverified`
rather than `ok`. Claiming a check you did not run is the one thing this section
forbids outright.

#### `stale-audio`

The digest, or `channels`, `sampleCount` or `durationMs` computed from the
stream, disagrees with `integrity`. Any one mismatch is enough. This usually means the
file was reprocessed or remuxed, not tampered with. The consumer MUST NOT
delete, hide or refuse to render the transcript, MUST NOT make the user
re-import the file, and SHOULD offer plain playback as an alternative. It SHOULD
show a message equivalent to:

```text
The audio in this file does not match the transcript recorded with it.
The transcript is shown as it was written; it may describe a different recording.
```

#### `ok`

Every manifest check passed, the audio digest and shape were computed from
the stream, and every one of them matched.

#### Where the hard check lives

Producers MUST fail closed. A producer MUST recompute the integrity block from
the file it is about to publish and MUST NOT publish one whose digest or shape
fields disagree with its own manifest. A `stale-audio` file should be impossible
to create, so a reader that meets one is looking at damage done afterwards, and
the transcript is still the best thing it has.

### When a tag and the manifest disagree

Most `CASSINI_*` tags duplicate a manifest value so that `ffprobe` shows
something before anything is decoded. **The manifest is the record and the
tags are the copy.** Once a consumer has the manifest it MUST use the
manifest's value, and SHOULD report the disagreement. A disagreement is not an
error.

Three exceptions:

- The manifest's own `CASSINI_PAYLOAD_*` descriptors have no manifest
  counterpart. For the manifest, the tags are the record.
- `CASSINI_FORMAT` is checked before any manifest exists. If it disagrees with
  `version`, the file is `invalid-cassini-metadata`.
- If `CASSINI_AUDIO_OPUS_SHA256` and `integrity.opusAudioSha256` disagree,
  there is no single claim to verify. The file is `unverified`, not `ok`.

### Casual inspection

A curious person with `ffprobe` and no documentation should be able to work
the format out. The tags they will see include `CASSINI_FORMAT`,
`CASSINI_PAYLOAD_ENCODING` and `CASSINI_DECODE_HINT`.

```bash
ffprobe -v error -show_entries stream_tags -of json meeting.opus
```

The manifest, decoded in a few lines:

```python
import base64, gzip, json, subprocess, sys

probe = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries",
                                 "stream_tags", "-of", "json", sys.argv[1]], text=True)
tags = {}
for stream in json.loads(probe).get("streams", []):
    tags.update(stream.get("tags", {}))
count = int(tags["CASSINI_PAYLOAD_CHUNK_COUNT"])
blob = "".join(tags[f"CASSINI_PAYLOAD_{i:03d}"] for i in range(count))
print(gzip.decompress(base64.urlsafe_b64decode(blob + "=" * (-len(blob) % 4))).decode())
```

That prints the index. A transcript body decodes the same way under its own
prefix. Neither this nor `ffprobe` verifies a digest, so a reader built from
them is `unverified`.

## Writing a file

Producers MUST:

- produce valid Ogg Opus;
- write every tag under [Cassini descriptor tags](#cassini-descriptor-tags);
- embed a manifest that validates against the schema;
- compute `CASSINI_AUDIO_OPUS_SHA256` over the canonical packet stream;
- keep summary tags and manifest in agreement;
- re-read the file they wrote and refuse to ship one whose digest or shape
  disagrees with its own manifest.

Producers SHOULD write compact JSON, keep the raw transcript even when a cleaned
one exists, and keep the manifest an index rather than a container.

A file SHOULD carry the meeting's identifying fields, the speaker table, the
canonical word transcript as its own chunk set, and optionally a readable
transcript and chapters. It SHOULD NOT carry search indexes, build products or
captions, which are derivable.

## Rationale

**Why not one binary blob tag.** The format should be legible. Explicit
encoding, integrity and count tags plus a decode hint make the metadata
self-describing enough that a curious user can decode it without reading source
code.

**Why gzip.** Browsers inflate it natively, the payload is small enough for it to
work well, and it decodes from a shell. A denser profile would be a new
`ENCODING` value, not an undocumented variation.

**Rejected alternatives.** A ZIP-like package: not playable in ordinary players.
MP4/M4A: Ogg/OpusTags is easier to inspect from the command line. WebM: less
obviously "just an audio file". Raw JSON in tags: bloat for no gain at this
size.

### Why `.meeting` is not a contract

The build pipeline stages a `.meeting` bundle directory with `cassini.json` and
`manifest.json`. These are build scratch. The only durable deliverable is the
`.opus` file. Do not treat the bundle as a stable interface.

How the reference operator guarantees a sealed, verified `.opus` exists before
anything downstream uses it is an implementation concern, recorded in
[`design/operator-sealing.md`](design/operator-sealing.md).
