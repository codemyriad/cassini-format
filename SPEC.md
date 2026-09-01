# Cassini Portable Meeting Format

Date: 2026-09-01

Status: published, version 1

A Cassini portable meeting is an ordinary Ogg Opus file that carries its own
word-timestamped transcript, speaker table and provenance inside its OpusTags
comment header, as gzip-compressed base64url JSON split across numbered tags. An
audio player that knows none of this plays it and ignores the rest.

> [`ERRATA.md`](ERRATA.md) records where the reference implementation and the
> published schemas do not yet do what this document requires. It is short, and
> it is the difference between a reader that works against real files and one
> that works against the prose.

<!-- spec:part v1 -->

## What this is

### Goal

Define one user-facing meeting file that is:

- one normal file
- directly playable as audio
- portable and easy to share
- rich enough for Cassini to reopen with transcript, speakers, and search

This format is the contract that both Cassini producers and Cassini consumers
should implement.

The `.opus` portable meeting file is the **one canonical, user-facing format**
and the only durable, published Cassini contract. The producer now emits
`org.cassini.portable-meeting/1`. Two shapes came before it, both used only
inside Cassini and neither ever published; they are kept in
[`spec/drafts/`](spec/drafts/) and are not part of this document. The intermediate `.meeting` bundle directory
(with its `cassini.json` and `manifest.json`) is transient build scratch, not
a deliverable — see [Why `.meeting` is not a contract](#why-meeting-is-not-a-contract).

### Decision

Cassini portable meeting files use:

- file extension: `.opus`
- container: Ogg
- audio codec: Opus
- embedded metadata: OpusTags comments
- embedded rich payload: UTF-8 JSON, `gzip` compressed, `base64url` encoded, split across numbered tags

Example filename:

```text
2026-03-11 Weekly Sync.opus
```

### Why this shape

This format optimizes for the user workflow:

- move one file around
- play it in ordinary audio players
- open it in Cassini and get the transcript and meeting structure back

It also keeps the format legible to a casual observer because the file exposes:

- ordinary audio playback
- plain-text metadata keys
- explicit instructions for decoding the embedded payload

### Notation

This document defines:

- required behavior with `MUST`
- recommended behavior with `SHOULD`
- optional behavior with `MAY`

### Implementing this

Read these in this order. Each settles something the next one assumes.

1. **This document** — the tag set, the two metadata layers, the chunking rules,
   the trust states, and what a consumer does in each of them.
2. **The manifest schema for the file's version**:
   [`spec/cassini-portable-meeting-manifest-v1.schema.json`](spec/cassini-portable-meeting-manifest-v1.schema.json)
   for files carrying `CASSINI_FORMAT=org.cassini.portable-meeting/1`. The
   schema is the authority on
   member names, types and required lists; where its constraints and this
   document's prose disagree, the schema is right.
3. [`spec/cassini-words-v1.md`](spec/cassini-words-v1.md) and its schema — the
   transcript body: what a `CASSINI_TX_<UPPER_ID>_PAYLOAD_` chunk set decodes
   to, and what a v1 manifest's inline `transcript` holds.
4. [`spec/cassini-opus-audio-integrity-v1.md`](spec/cassini-opus-audio-integrity-v1.md)
   — the canonical byte stream behind `CASSINI_AUDIO_OPUS_SHA256`. Needed when
   computing or verifying the audio digest.

The `CASSINI_PAYLOAD_SCHEMA` value is a version identifier, not a location.
`cassini.local` is a `.local` name, reserved for local-network name resolution;
resolving it does not reach a Cassini server, and on some networks it reaches
whatever else answers. Consumers MUST compare the value as a string and MUST NOT
fetch it.

#### What this format inherits rather than redefines

A Cassini portable meeting is an ordinary Ogg Opus file. Everything about the
container, the codec and the comment header comes from existing specifications
and is not restated here. An implementer needs all of the following, and this
document is not a substitute for any of it.

| What you need | Where it is defined |
|---|---|
| Ogg page header: the `OggS` capture pattern, the byte offsets of granule position, serial number, sequence number, CRC and segment count, and the `header_type` flags — `0x01` continued packet, `0x02` beginning of stream, `0x04` end of stream | RFC 3533 section 6 |
| Segmentation and lacing: a lacing value of 255 means the packet continues into the next segment, a value below 255 ends it, and a packet whose length is an exact multiple of 255 is terminated by a lacing value of 0 | RFC 3533 section 5 |
| Packet organisation: `OpusHead` alone on the beginning-of-stream page; the comment header is the **second** logical packet, MAY span several pages, and MUST finish the page on which it completes; audio data begins on a fresh page | RFC 7845 section 3 |
| `OpusHead` fields: version at offset 8, output channel count at 9, pre-skip as an unsigned little-endian 16-bit integer at 10–11, input sample rate at 12–15, output gain at 16–17, channel mapping family at 18, optional mapping table after | RFC 7845 sections 5.1 and 5.1.1 |
| `OpusTags` layout: the 8-octet `OpusTags` magic, an unsigned little-endian 32-bit vendor length, the vendor string, an unsigned little-endian 32-bit comment count, then that many comments each prefixed by its own unsigned little-endian 32-bit length. There is no Vorbis framing bit. | RFC 7845 section 5.2 |
| That each comment is a UTF-8 `NAME=value` string | RFC 7845 section 5.2.1, deferring to the Vorbis comment specification |
| That a field name is case-insensitive ASCII, that the first `=` is the separator, and that a name MAY occur more than once | the Vorbis comment specification, "Comment encoding → Content vector format" |
| That a reader MAY ignore comments not fully inside the first 61,440 octets of the comment header — which is what makes [Comment order](#comment-order) worth reading | RFC 7845 section 5.2 |
| Opus packet duration from the TOC byte, and the frame-count rules including "M MUST NOT be zero" and that a packet's audio duration MUST NOT exceed 120 ms | RFC 6716 sections 3.1 and 3.2.5 |
| base64url — the URL- and filename-safe alphabet, using `-` and `_` | RFC 4648 section 5 |
| gzip | RFC 1952 |

**One exception, because upstream is incomplete.** RFC 3533 section 6 specifies
the Ogg page CRC as *"a 4 Byte field containing a 32 bit CRC checksum of the
page (including header with zero CRC field and page content). The generator
polynomial is 0x04c11db7"* — and stops. That is not enough to compute one, and
the missing parameters are not the common defaults.
[`spec/cassini-opus-audio-integrity-v1.md`](spec/cassini-opus-audio-integrity-v1.md)
makes a CRC failure a reason to reject a stream, so a consumer verifying
`CASSINI_AUDIO_OPUS_SHA256` has to compute one.

The full parameters, as every Cassini file uses them: **generator polynomial
`0x04c11db7`, initial value `0`, no input or output bit reflection, no final
XOR**, computed over the whole page with the four CRC bytes themselves set to
zero. This is *not* the CRC-32 that `zlib.crc32` and most standard libraries
provide, which is reflected with an initial value of `0xFFFFFFFF` and a final
XOR. Check an implementation against the first page of any Cassini file: on the
published demo the stored value is `0x530297d0`, these parameters reproduce it,
and `zlib.crc32` returns `0x753f3847`.

### Versions, and what to implement

This document defines three wire versions, and every file ever written carries
one of them. Producers MUST write `org.cassini.portable-meeting/1`. Consumers
MUST read `/1`, `/2` and `/3`: files in people's hands stay there, and a
consumer that accepts only the current version rejects most of what exists.

Every section of this document describes the one published version. Nothing
here is version-conditional.

### Extensibility

This format is meant to grow without a version bump, so the rule for anything a
consumer does not recognise is: ignore it and carry on.

- Consumers MUST ignore an OpusTags comment whose field name they do not
  recognise, and MUST NOT treat its presence as an error.
- Consumers MUST ignore a manifest member they do not recognise, at any depth,
  and MUST NOT treat its presence as an error.
- A tool that rewrites a file's tags MUST carry unrecognised tags forward
  unchanged, and a tool that rewrites the manifest MUST carry unrecognised
  members forward unchanged. Dropping what you did not understand is how a
  format loses data another tool put there on purpose.

Two objects are the exception and are closed: `integrity`, and every
`payloadRef`. Every member of those is an instruction — for reassembling bytes,
or for deciding whether this audio and this transcript belong together — so an
unrecognised member there is a decode or verification failure, not a lost hint.
A consumer that ignored an unrecognised digest field would report a file as
verified while ignoring the field that defines its identity. Adding a member to
either object is a new major version, and that is the deliberate price of the
rule.

The published schemas say the same thing: those two objects are closed, and
every other object accepts members it does not declare. The three provenance
maps look closed and are not — `additionalProperties` there is the schema of a
map *value*, keyed by transcript id, not a bar on new keys.

Ignoring a member does not mean the file may be anything. A member this document
*does* define keeps its meaning: a consumer MUST NOT accept `version` as a
string because it ignores what it does not recognise, and MUST NOT read a v1
file's single `provenance.speechToText` object as a v2/v3 map.

#### Private use

Field names beginning with `X_`, and the manifest member `x`, are reserved for
private use. This format will never define either, so a producer can put its own
data in a file with no risk that a later revision collides with it.

- A private tag SHOULD be named `X_<OWNER>_<NAME>`, where `<OWNER>` comes from a
  domain the producer controls, upper-cased, with every character outside `A-Z`
  and `0-9` replaced by `_`. So `example.com` becomes `EXAMPLE_COM` and a tag
  reads `X_EXAMPLE_COM_TICKET=OPS-14`. Like every other tag name, it is matched
  case-insensitively.
- The manifest member `x` is a root-level object keyed by that owner, using the
  domain itself: `"x": {"example.com": {"ticket": "OPS-14"}}`. Private data goes
  under `x` and nowhere else, so that a tool publishing a recording outside the
  organisation that made it can strip all of it with one deletion and cannot
  miss one a colleague added at a depth nobody documented.

Consumers MUST ignore private data they do not own, exactly as they ignore
anything else they do not recognise. Note that editing `x` changes the manifest
bytes, so a tool that strips it MUST recompute `CASSINI_PAYLOAD_SHA256` and
`CASSINI_PAYLOAD_RAW_BYTES` or the file becomes unreadable.

#### Reserved for later

The top-level manifest member `payloads` and the tag prefix `CASSINI_PL_` are
reserved for a later revision, which will use them to carry payloads that are
not transcripts. Producers MUST NOT write either until that revision defines
them. A consumer that meets one MUST ignore it under the rule above, not reject
the file.

### File identification

A file is a Cassini portable meeting file when all of the following are true:

1. the container is Ogg Opus
2. its OpusTags comment vector carries `CASSINI_FORMAT`
3. its OpusTags comment vector carries a complete payload descriptor

A **payload descriptor** is the shortest set of tags that says both "this is a
Cassini file" and "here is how to decode it". It is exactly these four, and a
producer MUST write all of them:

- `CASSINI_FORMAT` — the wire version, `org.cassini.portable-meeting/<major>`
- `CASSINI_PAYLOAD_ENCODING` — how to turn the concatenated chunks back into
  bytes
- `CASSINI_PAYLOAD_CHUNK_COUNT` — a decimal integer of at least 1
- `CASSINI_PAYLOAD_000` through `CASSINI_PAYLOAD_<CHUNK_COUNT-1>` — every index
  present, none of them empty

Nothing else is part of the test. `CASSINI_PAYLOAD_SHA256`,
`CASSINI_PAYLOAD_RAW_BYTES`, `CASSINI_PAYLOAD_GZIP_BYTES`,
`CASSINI_PAYLOAD_MIME`, `CASSINI_PAYLOAD_SCHEMA` and `CASSINI_PROFILE` are
REQUIRED of producers, and are checks a consumer performs on a payload it has
already identified — not part of deciding whether it has one.

This document defines one version, `org.cassini.portable-meeting/1`.

If `CASSINI_FORMAT` is absent, consumers MUST treat the file as plain audio and
MUST NOT report an error: state `plain-audio` under
[Trust and integrity](#trust-and-integrity).

If `CASSINI_FORMAT` is present and names a major version this consumer does not
implement, the consumer MUST play the audio and MUST NOT refuse the file — the
Opus stream is valid whatever the metadata says. That is state
`unknown-cassini-format`, and what a consumer MAY still read from such a file is
defined there.

If `CASSINI_FORMAT` is present and the descriptor is incomplete, the file is a
Cassini file whose metadata is damaged: state `invalid-cassini-metadata`.

### Audio profile

#### Required

Portable meeting files MUST use:

- Ogg container
- Opus audio codec
- sample rate field set to `48000`

#### Recommended

Producers SHOULD write:

- mono audio for normal speech-first meeting archives
- stereo only when preserving stereo content is intentional
- one final continuous playable audio program

## The two metadata layers

The file MUST expose two metadata layers:

1. human-readable summary tags
2. structured Cassini payload tags

### Reading the comment vector

The tags are Vorbis comments in the `OpusTags` packet, which is the second
logical packet of the Ogg stream and MAY span several Ogg pages. A consumer MUST
reassemble the whole packet before parsing it — the run of lacing segments
ending in a segment shorter than 255, continued onto pages whose header type
flags continuation. Taking "the second page" instead of "the second packet"
truncates the comment list on any file whose comment header exceeds one page;
real Cassini headers reach 313,202 octets across five pages.

A consumer MUST read every comment in the vector. It MUST NOT apply the
allowance in RFC 7845 section 5.2, which lets a generic Opus implementation
"ignore individual comments that are not fully contained within the first 61,440
octets of the comment header": on a file with a long transcript the tags without
which nothing can be reassembled sit past that mark. See
[Comment order](#comment-order) for the producer's side of the same fact. A
consumer MUST still bound its own allocation, and MAY treat a comment header
larger than 120 MB as invalid, as RFC 7845 permits.

A consumer reading over HTTP MAY request only a prefix of the file, because the
comment header is at the front. If the returned range does not contain a
complete comment packet, the consumer MUST fetch more rather than parse what it
has.

Three rules the Vorbis comment format leaves open and Cassini pins down:

- **The separator is the first `=` in the comment.** The value MAY contain
  further `=` characters. Splitting on every `=` is wrong.
- **Field names are case-insensitive.** Producers MUST write every `CASSINI_*`
  name in upper case. Consumers MUST fold ASCII case before comparing: a file
  whose names have been lower-cased by a metadata editor is legal and MUST still
  read. Case folding applies to the **name** only; a value — a hex digest, a
  base64url chunk — MUST be compared and used exactly as written. Producers MUST
  NOT write two comments whose names differ only in case, and a tool rewriting a
  tag on a file it did not write MUST replace the spelling already in the file
  rather than add a second comment under the canonical spelling.
- **A field name MAY occur more than once, and Cassini never writes one twice.**
  Producers MUST NOT repeat a `CASSINI_*` name. A consumer that can see the
  repeat MUST NOT join the values and MUST NOT silently pick one: for any tag
  whose value is load-bearing — a chunk, a digest, a count, `CASSINI_FORMAT` —
  it MUST report `invalid-cassini-metadata`. For a mirror tag it SHOULD prefer
  the manifest's value and report the repeat. A consumer that reaches the tags
  through a tool which merges repeated names cannot detect this condition;
  such a reader is still conforming, and in practice the merged value fails its
  own digest check.

`ENCODER` and the OpusTags vendor string are the muxer's, not the producer's:
ffmpeg's Ogg muxer writes `encoder=Lavf<version>` in lower case whatever the
producer asked for, and drops a requested `ENCODER` entirely under
`-fflags +bitexact`. The upper-case rule above is scoped to `CASSINI_*` names
for that reason.

### Standard tags

Producers SHOULD write ordinary tags that generic tools can display:

- `TITLE`
- `DATE`
- `DESCRIPTION`
- `ENCODER`
- `LANGUAGE`

Recommended `DESCRIPTION` template:

```text
Cassini portable meeting file. Decode CASSINI_PAYLOAD_*: base64url -> gzip -> UTF-8 JSON.
```

### Cassini descriptor tags

These tags are REQUIRED. The audio identity contract is described under
[Audio integrity](#audio-integrity).

Identity:

- `CASSINI_FORMAT=org.cassini.portable-meeting/1`
- `CASSINI_PROFILE=ogg-opus`

The manifest chunk set:

- `CASSINI_PAYLOAD_MIME=application/vnd.cassini.portable-meeting+json`
- `CASSINI_PAYLOAD_ENCODING=base64url+gzip+utf8json`
- `CASSINI_PAYLOAD_SCHEMA=https://cassini.local/spec/cassini-portable-meeting-manifest-v1.schema.json`
- `CASSINI_PAYLOAD_CHUNK_COUNT=<decimal integer, 1 or more>`
- `CASSINI_PAYLOAD_SHA256=<lowercase hex sha256 of the decompressed UTF-8 JSON bytes>`
- `CASSINI_PAYLOAD_RAW_BYTES=<decimal integer>`
- `CASSINI_PAYLOAD_GZIP_BYTES=<decimal integer>`
- `CASSINI_PAYLOAD_000`..`CASSINI_PAYLOAD_<N-1>` — the chunks themselves; see
  [Chunk sets](#chunk-sets)

The transcript index. A v3 file carries at least one transcript, and each one's
body lives in its own chunk set, so these are what make a v3 file readable at
all:

- `CASSINI_TRANSCRIPT_IDS=<the ids in the manifest index, comma-separated, no spaces>`
- `CASSINI_TRANSCRIPT_DEFAULT=<the id of the transcript a viewer opens first>`
- and, for each id, its own chunk set: the six descriptors
  `CASSINI_TX_<UPPER_ID>_PAYLOAD_MIME`, `_ENCODING`, `_CHUNK_COUNT`, `_SHA256`,
  `_RAW_BYTES`, `_GZIP_BYTES`, plus `_000`..`_<N-1>`. The shape is defined under
  [Transcripts and their chunk sets](#transcripts-and-their-chunk-sets).

`CASSINI_TRANSCRIPT_IDS` and `CASSINI_TRANSCRIPT_DEFAULT` are **copies** of what
the manifest already says, written so that a reader holding only `ffprobe` can
see that a file has more than one transcript. The manifest is the record: see
[When a tag and the manifest disagree](#when-a-tag-and-the-manifest-disagree).
`CASSINI_TRANSCRIPT_IDS` is written in sorted order while `transcripts[]` stays
in the producer's order, so a consumer MUST compare them as sets and MUST NOT
require the same order.

Audio shape and identity:

- `CASSINI_AUDIO_SAMPLE_RATE=48000` — a constant, not a measurement: Opus always
  decodes at 48 kHz, whatever the original input rate was
- `CASSINI_AUDIO_CHANNELS=<1 or 2>`
- `CASSINI_AUDIO_SAMPLE_COUNT=<decimal integer>` — the normalized playable
  sample count defined in
  [`spec/cassini-opus-audio-integrity-v1.md`](spec/cassini-opus-audio-integrity-v1.md):
  packet durations summed at 48 kHz, minus pre-skip, clamped to
  `finalGranule - preSkip` when that is smaller
- `CASSINI_AUDIO_DURATION_MS=<decimal integer>` — `sampleCount * 1000 / 48000`
  in integer arithmetic, truncated toward zero, never rounded
- `CASSINI_AUDIO_OPUS_SHA256=<lowercase hex sha256 of the canonical compressed Opus audio>`
- `CASSINI_AUDIO_MATCH_POLICY=exact-opus-audio-v1`

And the instruction for a reader who has none of this document:

- `CASSINI_DECODE_HINT=Concatenate CASSINI_PAYLOAD_000..N for the manifest; for a transcript body concatenate CASSINI_TX_<ID>_PAYLOAD_000..N. Each chunk set: base64url decode, gzip decompress, parse UTF-8 JSON.`

Every one of these MUST carry a non-empty value. A producer that has no value
for a REQUIRED tag has a file it cannot write; it MUST NOT write the tag blank
and MUST NOT omit it.

Writers MUST NOT
reinterpret an older file's PCM digest as a compressed-audio digest, and MUST
NOT relabel an old file's `CASSINI_AUDIO_MATCH_POLICY` while retagging it.

### Comment order

RFC 7845 section 5.2 lets an Opus implementation "ignore individual comments
that are not fully contained within the first 61,440 octets of the comment
header". A Cassini payload routinely exceeds that. Comment-header cost measured
across the nine shipped v1 files runs 3,598 to 7,039 octets per minute of
meeting, so roughly nine to seventeen minutes fills the window:

| file | OpusTags packet | comments | past 61,440 |
|---|---|---|---|
| the published demo, a 4-minute meeting | 14,376 B | 37 | 0 |
| a 17-minute recording | 84,527 B | 48 | 23 |
| the largest v1 sample | 307,370 B | 102 | 77 |

**In practice nothing truncates, and this format accepts the risk.** Tested
against that 307 KB file: `ffmpeg -c copy`, an `.opus` to `.ogg` remux and a
mutagen round-trip each preserve all 102 comments,
`CASSINI_PAYLOAD_CHUNK_COUNT` and `CASSINI_PAYLOAD_SHA256` included. These files
are played, not edited. No existing file is in danger and nothing needs
repacking.

It is still worth knowing which tags sit where, because ASCII order is not the
order you would choose. `CASSINI_PAYLOAD_000` sorts before
`CASSINI_PAYLOAD_CHUNK_COUNT`, since `0` sorts before `C`, so sorting the whole
comment list writes the entire payload ahead of the descriptors that explain it.
On a 69-minute meeting that put the chunk count at byte 306,584 of a
307,370-octet header.

A new producer may as well write, and MAY write:

1. `CASSINI_FORMAT` first, ahead of every other comment it writes
2. then every other non-chunk comment — the remaining descriptors, the summary
   tags, the optional origin tags, `TITLE`, `DATE`, `DESCRIPTION` — in any order
   among themselves
3. then the numbered chunk tags: `CASSINI_PAYLOAD_000..N`, and each
   `CASSINI_TX_<UPPER_ID>_PAYLOAD_000..N`

It costs nothing: the non-chunk block is 1,388 octets on the largest file
measured and 1,898 on the v3 demo, two percent of the window, and it grows by
roughly 400 octets per additional transcript. What it buys is graceful
degradation instead of a cliff. A reader that does enforce the limit still
identifies the file, reads its title, date, speaker count, duration and audio
digest, and learns that a payload exists and how large it is, rather than seeing
an Ogg Opus file with unexplained base64 in it.

A muxer may append comments of its own after everything the producer asked for —
ffmpeg's Ogg muxer appends `encoder=Lavf<version>` — and that is fine: no
Cassini reader needs a comment the producer did not write.

Consumers MUST read the whole comment vector and MUST NOT enforce the
61,440-octet limit on a Cassini file; see
[Reading the comment vector](#reading-the-comment-vector). Consumers MUST NOT
depend on comment order for anything else: chunks are reassembled by the numeric
index in their tag name, never by position.

### Summary tags

Three tags carry a summary a reader can use before decoding anything:

- `CASSINI_MEETING_ID=<stable meeting id>`
- `CASSINI_CREATED_AT=<RFC3339 UTC timestamp>`
- `CASSINI_SPEAKER_COUNT=<decimal integer>`

Producers SHOULD write all three. Consumers MUST NOT require them: they are a
convenience copy of values the manifest already holds, and the manifest is the
record.

Earlier drafts of this document also recommended `CASSINI_WORD_COUNT`,
`CASSINI_TRANSCRIPT_LANGUAGE`, `LANGUAGE`, four `CASSINI_STT_*` tags, four
`CASSINI_READABLE_*` tags and a `CASSINI_ATTRIBUTION_*` family. **No file has
ever carried them.** They come from the v1 tag builder, which no longer has a
caller, so a consumer that depends on any of them fails on every real file. They
are not part of this version. The same values, where they exist at all, are in
the manifest's `provenance` and in each transcript entry.

If you want one of them back, it is an additive producer change and a line in
this section, not a version bump. Deciding that is
[freeze item 9](design/format-freeze-2026-08-28.md).


### Optional mirror tags

The following tags are OPTIONAL, and mirror the origin fields in the `meeting`
object. Each is emitted only when the value is known — absent, never empty,
because an empty `CASSINI_ROOM_ID` would read as "this meeting has a room whose
id is the empty string" and every consumer would have to check both presence and
emptiness.

- `CASSINI_ROOM_ID=rm_<16 lowercase hex>`
- `CASSINI_ROOM_NAME=<display name>` — legacy, no longer written; see below
- `CASSINI_JOB_ID=<producer job id>`
- `CASSINI_ATTEMPT_NUMBER=<decimal integer, 1-based>`

They are a convenience mirror for readers that are neither Go nor Node: the
values are already in the embedded manifest, but reading them out of it means
concatenating N chunks, base64url-decoding, gunzipping and parsing JSON — which
is a program, while these fall out of one `ffprobe -show_entries format_tags`
call. **The manifest is the record and these are the copy.** A tool that edits
one MUST edit the other; a consumer that finds them disagreeing SHOULD believe
the manifest, and [When a tag and the manifest disagree](#when-a-tag-and-the-manifest-disagree)
gives the rule in full.

## Chunk sets

A **chunk set** is how this format puts a document of any size into OpusTags
comments. It is a tag prefix `P` plus seven kinds of tag:

```text
P MIME          the media type of the decoded document
P ENCODING      how to get from the concatenated text back to bytes
P CHUNK_COUNT   how many numbered tags there are
P SHA256        lowercase hex sha256 of the decoded document's bytes
P RAW_BYTES     the decoded document's length in bytes
P GZIP_BYTES    the compressed length in bytes
P 000 .. P<N-1> the document itself
```

written as `CASSINI_PAYLOAD_MIME`, `CASSINI_PAYLOAD_000` and so on. A v3 file
contains at least two chunk sets: the manifest, whose prefix is always
`CASSINI_PAYLOAD_`, and one per transcript body, whose prefix is given by that
transcript's `payloadRef.prefix`.

Rules, identical for every chunk set:

- Indexing starts at `000`.
- The index is decimal, zero-padded to a **minimum** of three digits, using as
  many digits as the number needs and no more: `000`, `001`, … `999`, `1000`,
  `1001`. The width is per index, never per set. Consumers MUST parse the index
  as a number and MUST NOT assume a fixed-width field.
- The tags `P000` through `P<CHUNK_COUNT-1>` MUST all be present. A consumer
  MUST reassemble by generating those names and looking each one up — not by
  scanning for tags that look like chunks. A missing index makes the chunk set
  unreadable; a consumer MUST NOT concatenate across the gap.
- A chunk tag name MUST appear exactly once. A consumer that can see a repeat
  MUST treat the chunk set as unreadable rather than pick a value; see
  [Reading the comment vector](#reading-the-comment-vector).
- Higher-numbered chunk tags beyond `CHUNK_COUNT-1` are ignored, not an error:
  a rewriting tool that shortened a payload may have left them behind.
- Values are concatenated in **numeric index order**, with no separator, never
  in the order the comments appear in the file.
- The concatenation is the complete encoded text of the document. An individual
  chunk is not guaranteed to be decodable on its own — the split falls wherever
  the producer's chunk size lands. Consumers MUST concatenate first and decode
  once.
- Producers SHOULD limit each chunk value to at most `4096` characters. This is
  not required by Ogg, and nothing reads it as a boundary; it keeps the metadata
  readable in ordinary tools that print one tag per line.

**Which declaration wins.** For the manifest there is no manifest yet, so
`CASSINI_PAYLOAD_CHUNK_COUNT` and the other `CASSINI_PAYLOAD_*` descriptors are
the record. For a transcript body there is: `payloadRef` carries `prefix`,
`chunkCount`, `sha256`, `rawBytes`, `gzipBytes`, `mime` and `encoding`, all
required by the schema, and a consumer MUST take those seven values from
`payloadRef` and MUST NOT take them from the matching
`CASSINI_TX_<UPPER_ID>_PAYLOAD_*` tags. Those tags are a copy for `ffprobe`
users; a disagreement is a warning, not a failure.

Note for anyone writing a tool that rewrites chunk sets: `CASSINI_PAYLOAD_SCHEMA`,
`CASSINI_PAYLOAD_MIME` and the other descriptors all begin with
`CASSINI_PAYLOAD_`, which is also the manifest chunk set's prefix. A chunk tag
is the prefix followed by **digits only**; matching the prefix alone deletes
REQUIRED descriptors. The same trap applies to every
`CASSINI_TX_<UPPER_ID>_PAYLOAD_` set.

### Payload encoding

Every chunk set carries its document encoded the same way. The one encoding this
document defines is `base64url+gzip+utf8json`, and it means:

1. compact UTF-8 JSON bytes — no insignificant whitespace, no trailing newline,
   no byte-order mark. The chunk set's `SHA256` is the SHA-256 of exactly these
   bytes, before compression and before encoding.
2. `gzip` compressed (RFC 1952)
3. base64url encoded (RFC 4648 section 5), **unpadded**, with no line breaks
4. split across the numbered tags of that chunk set

Unpadded means the encoded text contains no `=`. Producers MUST write it
unpadded. Consumers MUST accept both padded and unpadded input: padded is the
default output of most languages' base64url encoders, and refusing it turns a
cosmetic difference into a lost transcript. A consumer MUST discard ASCII
whitespace anywhere in the concatenated text **before** deciding whether padding
is present or how much to add — a Vorbis comment value is arbitrary UTF-8 and
may legally contain a newline, and computing the padding from the unstripped
length is a bug that only shows up on some inputs.

`RAW_BYTES` and `GZIP_BYTES` are not decoration. A gzip stream can claim to be
small and inflate to gigabytes, and a consumer that inflates first and checks
afterwards has already allocated the memory: a 2 MB Cassini file can name a
200 MB payload. Consumers MUST stop inflating as soon as the output exceeds the
declared `RAW_BYTES`, and MUST treat the result as damaged metadata rather than
inflating to completion and comparing. Where no size is declared, a consumer
MUST apply an absolute ceiling of its own. Consumers SHOULD apply one anyway, in
case the declared value is itself absurd.

A consumer that has inflated within the bound MUST check the declared SHA-256
before believing any field of the result. An absent digest is not a passed
check: see [Trust and integrity](#trust-and-integrity), state `unverified`.

A consumer MUST NOT decode a chunk set whose declared `ENCODING` it does not
implement. The encoding tag exists so a decoder knows what to do before it does
it; ignoring it turns a future encoding into silent garbage.

`gzip` is the encoding because browser decompression is standard, the payload is
small enough for it to work well, and the result is still easy to decode from a
shell. If Cassini later needs a denser archival profile, that is a new
`ENCODING` value or a new `profile`, not an undocumented variation.

## Reading a file

This is the read path in order. A consumer that performs these steps reads every
file this format defines.

1. **Find the tags.** Reassemble the `OpusTags` packet and parse the comment
   vector: [Reading the comment vector](#reading-the-comment-vector).
2. **Decide what the file is.** [File identification](#file-identification). No
   `CASSINI_FORMAT` is `plain-audio` and is not an error.
3. **Reassemble the manifest.** The chunk set with prefix `CASSINI_PAYLOAD_`:
   [Chunk sets](#chunk-sets).
4. **Decode and verify it.** [Payload encoding](#payload-encoding): bound the
   inflate, then check the declared digest and byte counts before believing any
   field of the result.
5. **Read the manifest.** Check `kind` and `version`:
   [Embedded manifest](#embedded-manifest). Ignore members you do not recognise:
   [Extensibility](#extensibility).
6. **Resolve which transcript to show.** See below.
7. **Decode that transcript's body.** Its chunk set, by the same rules as step 3
   and step 4, with `payloadRef` as the record for all seven of its declared
   values. The body format is
   [`spec/cassini-words-v1.md`](spec/cassini-words-v1.md).
8. **Decide whether to trust it, and say so.**
   [Trust and integrity](#trust-and-integrity). Every read ends in exactly one
   of the six states named there.

### Resolving a transcript

A v1 file carries one transcript inline at `manifest.transcript`, optionally
with `readableTranscript` and `displayTranscript` beside it. A v2 or v3 file
carries an index: `transcripts[]` for the word-timed transcripts and
`readableTranscripts[]` for the derived ones, each entry naming its own chunk
set. A consumer that synthesises a one-entry index from a v1 file reads all
three versions on one code path.

There are three slots a consumer fills — words, readable, display — and it fills
each the same way:

1. the first entry **for that slot**, in array order, whose `default` is `true`;
2. failing that, the first entry for that slot, in array order.

`readableTranscripts[]` holds both the readable and the display slot, so a
consumer MUST filter by `role` before applying that rule. Array order is
therefore normative: reordering `transcripts[]` changes what a user sees. A
consumer MUST NOT require a default to be flagged; zero flagged defaults is a
legal file.

When pairing a readable transcript with the words transcript on screen, a
consumer SHOULD prefer the entry whose `sourceTranscriptId` names the words
transcript it is showing, before falling back to the rule above. On a file with
two words transcripts, anything else shows the cleanup of one beside the words
of the other.

`CASSINI_TRANSCRIPT_IDS` and `CASSINI_TRANSCRIPT_DEFAULT` are copies. The
manifest is the list and the manifest resolves the default. A consumer MUST
ignore an id that appears in `CASSINI_TRANSCRIPT_IDS` but not in the manifest,
and MUST ignore a `CASSINI_TRANSCRIPT_DEFAULT` that names no manifest entry.
Where the tag and the flag both resolve and disagree, the manifest wins and the
consumer SHOULD say so.

An entry whose chunk set is missing or fails its checks makes **that transcript**
unavailable. A consumer MUST NOT fail the file for it: the other transcripts,
the speaker table and the meeting metadata are still good, and it SHOULD tell
the user which transcript it could not load.

### In general

Cassini consumers MUST:

- accept plain `.opus` files with no Cassini metadata as normal audio, silently
- keep playing the audio whatever else goes wrong: a file that played before a
  Cassini reader touched it MUST still play afterwards

Cassini consumers SHOULD:

- expose meeting title, date and speaker count before rendering any transcript —
  those are one small chunk set away and a transcript body may be many
- report every check they skipped, not only the ones they failed

### Trust and integrity

The `integrity` object exists so a consumer can tell whether the metadata in a
file still describes the audio in that file. It is a **join key, not a seal**:
it answers "do these two belong together?" and nothing else. It is not evidence
that the audio is authentic, that the transcript is accurate, or that neither
has been replaced by someone who also recomputed the digest.

Nothing below throws a transcript away. In the life of a real file the audio
does not change and the transcript does — reprocessing with a newer model is the
normal thing that happens to a meeting — so a reader that discards the
transcript when a check fails is wrong far more often than it is right. The hard
check belongs in the producer, which knows what it meant and can refuse to ship.
The consumer only knows that two numbers differ, and has a user in front of it.

A consumer MUST end every read in exactly one of these six states, and MUST make
the state visible to whoever called it. The names are normative, so that two
readers describe one file the same way.

#### `plain-audio`, no Cassini metadata

`CASSINI_FORMAT` is absent. Play the audio. This is the ordinary case for an
ordinary `.opus` file and MUST NOT be reported as an error.

#### `unknown-cassini-format`, a version this consumer does not implement

`CASSINI_FORMAT` is present and names a major version this document does not
define, or one this consumer has not implemented. The consumer MUST play the
audio and MUST NOT refuse the file: the Opus stream is valid whatever the
metadata says, and refusing it turns a forward-compatible file into a broken
one. It SHOULD say that the file carries meeting metadata in a version it cannot
read. It MAY decode the manifest anyway and show `meeting`, `audio` and
`speakers`, whose shape has not changed in any version — but it MUST NOT present
a transcript it does not understand as though it did.

#### `invalid-cassini-metadata`, present and unreadable

`CASSINI_FORMAT` is present and the metadata cannot be reconstructed: the
payload descriptor is incomplete, a chunk is missing or repeated, the declared
chunk count does not match the chunks present, the base64url or gzip decode
fails, the payload digest does not match the bytes recovered, the JSON does not
parse, `kind` is not `cassini-portable-meeting`, or `version` and
`CASSINI_FORMAT` disagree.

Play the audio. Say that the file carries Cassini metadata that could not be
read, and say which step failed. A consumer MUST NOT render a partially decoded
manifest, and MUST NOT refuse to play a file that plays.

#### `unverified`, present, readable, and not checked against the audio

The consumer did not check the audio, for any of these reasons:

- it has not read the audio bytes — a reader that fetches only the metadata
  prefix over a byte-range request is in this state by design, and so is a
  command-line tag tool
- it does not implement the verification path this file's version uses
- the file carries no audio digest to check against
- the digest in the manifest and the digest in the tags disagree, so there is no
  single claim to check

The consumer MUST open the file as a portable meeting and MUST show the
transcript. It MUST mark the metadata **unverified** wherever it presents it —
not only in a log or a details panel — and MUST NOT present the transcript as
checked.

A consumer that never verifies audio is conforming, and MUST report `unverified`
rather than `ok`. Claiming a check you did not run is the one thing this section
forbids outright.

#### `stale-audio`, present, readable, checked, and it does not match

The audio digest, or one of the shape fields, disagrees with the manifest.

The consumer MUST open the file as a portable meeting, MUST keep the transcript
and MUST show it. It MUST label it, and the label MUST stay attached wherever
the transcript is shown. It SHOULD name which check failed, because "the digest
differs" and "the duration differs by 7 ms" are different problems for whoever
has to fix the file. It SHOULD offer plain-audio playback as an alternative. It
MUST NOT delete, hide or refuse to render the transcript, and MUST NOT make the
user re-import the file to see it.

A mismatch usually means the file was reprocessed or remuxed, not that anyone
tampered with it. The user is the one who can tell; the consumer's job is to
give them the fact, not to make the decision for them.

Consumers SHOULD surface a message equivalent to:

```text
The audio in this file does not match the transcript recorded with it.
The transcript is shown as it was written; it may describe a different
recording.
```

#### `ok`, present, readable, checked, and it matches

Every check the consumer performed passed, and the audio digest was one of them.
Open the file as a full portable meeting.

#### Where the hard check lives

**Producers MUST fail closed.** A producer MUST recompute the integrity block
from the file it is about to publish — not from the input it encoded — and MUST
NOT publish a file whose digest, sample rate, channel count, sample count or
duration disagrees with its own manifest. The reference producer does exactly
this: it writes a candidate file, re-hashes it, compares, and returns an error
rather than committing a file that does not verify.

That asymmetry is what makes the consumer rules above safe. A `stale-audio` file
should be impossible to create, so a reader that meets one is looking at damage
that happened afterwards — and the transcript is still the best thing it has.

#### When a tag and the manifest disagree

Most `CASSINI_*` descriptor and summary tags duplicate a value that is also in
the manifest. They are there so a reader holding only `ffprobe` can see
something before it decodes anything. **The manifest is the record and the tags
are the copy.** Once a consumer has decoded the manifest it MUST use the
manifest's value and MUST discard the tag's, and it SHOULD report the
disagreement. A disagreement is not an error and MUST NOT fail the file: it
means a tool edited one layer and not the other.

Three exceptions:

- The manifest chunk set's own descriptors — `CASSINI_PAYLOAD_ENCODING`,
  `CASSINI_PAYLOAD_CHUNK_COUNT`, `CASSINI_PAYLOAD_SHA256`,
  `CASSINI_PAYLOAD_RAW_BYTES`, `CASSINI_PAYLOAD_GZIP_BYTES` — have no manifest
  counterpart. There is no manifest yet when a consumer reads them, so for the
  manifest the tags are the record.
- `CASSINI_FORMAT` decides whether the file is read at all, before any manifest
  exists. If it disagrees with the manifest's `version` the file is
  `invalid-cassini-metadata`, not a disagreement to resolve.
- The audio digest is not a mirror in the useful sense. If
  `CASSINI_AUDIO_OPUS_SHA256` and `integrity.opusAudioSha256` disagree there is
  no single claim to verify against, and the file is `unverified` — not `ok`
  because the manifest happened to match the audio.

### Casual inspection

A casual file observer SHOULD be able to infer the format with tools such as:

```bash
ffprobe -v error -show_entries format_tags:stream_tags -of json meeting.opus
```

Expected visible cues:

- `CASSINI_FORMAT`
- `CASSINI_PAYLOAD_ENCODING`
- `CASSINI_DECODE_HINT`
- speaker and word counts
- human title/date tags

Manual decode flow:

```bash
python3 - <<'PY'
import base64, gzip, json, subprocess
import sys

path = sys.argv[1]
probe = subprocess.check_output([
    "ffprobe", "-v", "error",
    "-show_entries", "format_tags:stream_tags",
    "-of", "json", path,
], text=True)
doc = json.loads(probe)
tags = {}
tags.update(doc.get("format", {}).get("tags", {}))
for stream in doc.get("streams", []):
    tags.update(stream.get("tags", {}))
count = int(tags["CASSINI_PAYLOAD_CHUNK_COUNT"])
blob = "".join(tags[f"CASSINI_PAYLOAD_{i:03d}"] for i in range(count))
raw = gzip.decompress(base64.urlsafe_b64decode(blob + "=" * (-len(blob) % 4)))
print(raw.decode("utf-8"))
PY
./meeting.opus
```

That prints the manifest, which in v2 and v3 is an index: it names the
transcripts but does not contain them. A transcript body is a second chunk set
under its own prefix, decoded exactly the same way. Neither this snippet nor
`ffprobe` verifies a digest, so a reader built from them is `unverified`, never
`ok`.

## The manifest

### Embedded manifest

The decompressed `CASSINI_PAYLOAD_*` payload MUST be a JSON object. Which schema
it conforms to follows from its own `version` field:

There is one published version, and its schema is
[`spec/cassini-portable-meeting-manifest-v1.schema.json`](spec/cassini-portable-meeting-manifest-v1.schema.json).

`CASSINI_PAYLOAD_SCHEMA` names that schema as a URL, for a human reading the
tags. On any disagreement between that tag and `version`, `version` wins.

Producers MUST write `version: 1`. A consumer that meets a higher `version`
MUST NOT guess at it: see
[`unknown-cassini-format`](#unknown-cassini-format-a-version-this-consumer-does-not-implement).

Three members identify the document itself:

- `kind` — the literal string `cassini-portable-meeting`. A consumer that finds any other value MUST NOT
  treat the file as a portable meeting.
- `version` — the integer `1`. It MUST match the version in `CASSINI_FORMAT`. A consumer that finds the two
  disagreeing MUST NOT guess which is right: the file is
  `invalid-cassini-metadata`, per [Trust and integrity](#trust-and-integrity).
- `profile` — the literal string `ogg-opus`. A
  consumer that finds any other value MUST NOT treat the file as a portable
  meeting. A denser future profile would carry a new `profile` value and a new
  `version`, so a reader written today is right to refuse one.

A manifest also carries `meeting`, `audio`, `integrity` and `speakers`, and:

- `transcripts` — the index of the word-timed transcripts, one entry each, at
  least one entry. V3 has no top-level `transcript` object: each body lives in
  its own chunk set and the entry holds a `payloadRef` to it. See
  [Transcripts and their chunk sets](#transcripts-and-their-chunk-sets) for the
  entry shape.

and MAY also carry:

- `readableTranscripts` — the same index shape for the derived readable and
  display transcripts. Those never appear in `transcripts`, and a word-timed
  transcript never appears here.
- `provenance`
- `chapters`
- `summary`
- `attachments`
- `x` — private-use data; see [Extensibility](#extensibility)

#### The manifest is an index

In v2 and v3 the manifest does not contain the transcript; it points at it. In
the published demo the manifest is 2,127 bytes uncompressed and the single
transcript body it points at is 45,837. A consumer that needs only the title,
the date and the speaker list never decodes a transcript body at all.

### Manifest semantics

#### `meeting`

The `meeting` object identifies the meeting and carries its user-facing fields.

Required:

- `id` — a stable identifier for this recording. The reference producer derives
  it from the audio digest: `mtg_` followed by the 64 hex characters of
  `integrity.opusAudioSha256` in v3, and of `integrity.pcmSha256` in v1 and v2.
  A metadata-only retag therefore preserves the id; re-encoding the audio does
  not. Another producer MAY use any stable non-empty string, and consumers MUST
  NOT parse it.
- `title` — a non-empty display title.
- `createdAtUtc` — an RFC 3339 UTC timestamp: when the producing pipeline
  stamped this artifact. It is not when the meeting happened — that is
  `recordedAtLocal` — and it is not necessarily when the file was packed. In
  every file the reference producer writes it holds the same value as
  `processedAtUtc`, and in shipped v1 files it is two weeks later than the
  recording.
- `durationMs` — the playable duration in milliseconds.

Optional:

- `recordedAtLocal` — wall-clock time at the recording site. Deliberately not
  constrained to a UTC format: the local time is the point.
- `processedAtUtc` — when the pipeline processed the recording.
- `language` — a BCP-47 tag for the meeting. The reference producer populates it
  on no path, so a consumer MUST NOT rely on it being present.
- `summary` — reserved. No producer writes it and no meaning has been assigned.
  Distinct from the top-level `summary` member described below.

It MAY also carry where the meeting came from. All four are optional, and a
meeting with none of them is an ordinary state, not a broken one:

- `roomId` — the conversation the meeting was recorded in, as a **deterministic
  one-way derivation** of that room's identity, shaped `rm_<16 lowercase hex>`.
  Never the identity itself: for a Nextcloud Talk recording it derives from the
  conversation token, and for a public conversation that token is also the link
  that joins it — so publishing it alongside a recording would turn "may read a
  past recording" into "may join the live conversation". Producers MUST NOT
  write a raw room token into this file, in this field or any other.
- `roomName` — **LEGACY, read-only.** The room's display name frozen at record
  time. Producers stopped writing it: a display name is editable and a published
  recording is not, so honouring a rename would mean rewriting every artifact
  that room ever produced. The name at record time is still available as the
  `title`; the room's *current* name belongs wherever the producer keeps mutable
  metadata. Consumers MUST still read it, because files written before the
  change carry it.
- `jobId` — the producer job that made this artifact. Optional; a file packed by
  hand has none.
- `attemptNumber` — which attempt of that job, 1-based. Absent means unknown, so
  a consumer MUST treat a non-positive value as absent rather than as an attempt.

#### `audio`

The `audio` object MUST describe the playable audio actually stored in the file.
All six fields are required:

- `container` — `ogg`
- `codec` — `opus`
- `sampleRate` — `48000`
- `channels` — `1` or `2`
- `sampleCount` — playable samples at 48 kHz
- `durationMs`

#### `integrity`

The `integrity` object lets a consumer tell whether this manifest still
describes the audio in the file. What it does with the answer is defined under
[Trust and integrity](#trust-and-integrity).

Required in v3:

- `matchPolicy` — `exact-opus-audio-v1`
- `opusAudioSha256` — 64 lowercase hex characters, over the canonical
  compressed Opus audio defined in
  [`spec/cassini-opus-audio-integrity-v1.md`](spec/cassini-opus-audio-integrity-v1.md)
- `sampleRate`, `channels`, `sampleCount`, `durationMs` — the shape fields,
  which MUST equal their counterparts in `audio`

`containerSha256` is declared optional by the v1 and v2 schemas and is written
by no producer. Consumers MUST ignore it.

#### `speakers`

The `speakers` array carries the speaker table that transcript items refer to.
Each entry has an `id` and a `label`, both non-empty strings. The array MAY be
empty when no speaker was identified; an empty table is not an error.

Producers MUST write an entry for every speaker their transcript bodies name.

What a consumer does with a `speaker` that matches no entry is settled in
[`spec/cassini-words-v1.md`](spec/cassini-words-v1.md) and not here: the item is
still transcript content and MUST be rendered under an unknown speaker rather
than dropped.

#### `transcripts`

`transcripts` is the index of the raw transcripts in this file. It MUST contain
at least one entry. Each entry describes one transcript and names the chunk set
that carries its body; the entry shape and the tag layout are defined under
[Transcripts and their chunk sets](#transcripts-and-their-chunk-sets).

The transcript bodies are the canonical transcript of this recording. Derived
views — a readable transcript, captions, a summary — MUST be treated as optional
derived material, regenerable from the canonical bodies and never a substitute
for them.

`readableTranscripts` is the optional index of those derived readable
transcripts. Each entry MUST name the raw transcript it derives from, in
`sourceTranscriptId`.

#### `provenance`

The optional `provenance` object records which systems produced each metadata
layer, so a user can inspect a file and see what made it.

In v2 and v3, the first three members are **maps keyed by transcript id**, not
single objects. A transcript with `id: "canary"` resolves to
`provenance.speechToText.canary`. A consumer that reads more than one version
MUST handle both shapes; unmarshalling a v2/v3 map into a v1 single object
succeeds silently and yields empty values, which is the failure this section
exists to prevent.

- `speechToText` — map of transcript id to processing step. Producers SHOULD
  include an entry for every `transcripts[]` entry.
- `readableCleanup` — map, same keying, for `readableTranscripts[]` entries with
  role `readable-cleanup`.
- `displayTranscript` — map, same keying, for role `display`.
- `meetingSummary` — a single processing step for the meeting summary, if one
  was generated.
- `attribution` — how cross-track speaker attribution ran. Required members
  `ran`, `mode`, `wordsMeasured`, `wordsFlagged`, `wordsDropped`; optional
  `reason` and `thresholdDb`. The reference producer writes `mode` as
  `annotate`, `drop` or `disabled`; the member is an open string, so a consumer
  MUST NOT reject a value it does not recognise. In `drop` mode the flagged
  words were deleted before publication and this record is the only surviving
  trace that they existed.
- `wordTimings` — one boolean, `endsBoundedByAudio`. **A consumer keys off its
  presence, not its value.** Absent means the word ends are unvouched for: they
  may have come from each word's last token, and a token that is a trailing
  punctuation mark is stamped at the next acoustic onset, so a sentence-final
  word can run for seconds over silence. A repair that clips an over-long word
  is appropriate on such a file, and destroys correct timing on a file that
  carries the record.

`meetingSummary`, `attribution` and `wordTimings` were added at v2. A v1
manifest carries none of them, and its `speechToText`, `readableCleanup` and
`displayTranscript` are single processing steps rather than maps, because a v1
file has exactly one transcript.

A processing step has optional string members and nothing required: `backend`,
`engine`, `model`, `device`, `language`, `source`, `version`, and the two
described next. `source` in practice takes `generated`, `embedded` or
`disabled`. `language` is the model's language, which is not necessarily the
transcript's. Producers MUST NOT record a service endpoint in a processing step
— no URL, no hostname, no address — in `baseUrl`, in `host`, or in any other
member: where a model ran is not a property of the recording, and this file
carries what it holds in cleartext to everyone who receives it. A consumer that
meets `baseUrl` or `host` in an older file SHOULD NOT display or forward them.

#### `chapters`, `summary`, `attachments`

All three are optional.

`chapters` entries carry `startMs` and `title`; `endMs` was added at v2. No
producer writes chapters today.

`summary` is metadata **about** the meeting summary, not the summary itself.
When the reference producer generated one it writes `format: "markdown"`,
`templateVersion: "v0"`, and `model` when the summarising model is known. The
member is deliberately open: a consumer MUST ignore keys it does not recognise.

`attachments` carries the summary itself and anything else that travels whole.
An attachment carries its bytes in `contentBase64`, which is **standard base64,
not base64url** — the one place in the format where the alphabet differs. The
meeting's summary markdown, when there is one, travels as an attachment with
`name: "summary.md"` and `mime: "text/markdown"`.

### Transcripts and their chunk sets

Each entry in `transcripts[]` and `readableTranscripts[]` describes one
transcript and names the chunk set that carries its body:

```jsonc
{
  "id":      "canary",                    // ^[a-z0-9][a-z0-9-]{0,31}$, unique in file
  "role":    "raw-asr",                   // raw-asr | human-corrected | translation
  "default": true,                        // at most one per slot; see below
  "format":  "cassini.words.v1",
  "language": "en",
  "wordCount": 9224,
  "createdAtUtc": "2026-05-12T...",
  "payloadRef": {
    "prefix":     "CASSINI_TX_CANARY_PAYLOAD_",
    "chunkCount": 14,
    "sha256":     "...",                  // sha256 of decompressed body JSON
    "rawBytes":   718432,
    "gzipBytes":  221110,
    "mime":       "application/vnd.cassini.transcript-words+json",
    "encoding":   "base64url+gzip+utf8json"
  }
}
```

Readable transcripts use the same shape, with `role` from `{readable-cleanup,
display}` and a required `sourceTranscriptId`. A word-timed entry with role
`human-corrected` or `translation` also carries one; an entry with role
`raw-asr` MUST NOT. In both arrays the id MUST name a transcript this file
declares.

The transcript `id` doubles as the provenance map key. A transcript entry with
`id: "canary"` resolves to `provenance.speechToText.canary`.

The tags that carry a transcript body:

```text
# discoverable from ffprobe alone
CASSINI_TRANSCRIPT_IDS=<comma-separated ids>
CASSINI_TRANSCRIPT_DEFAULT=<id of the transcript a viewer opens first>

# one chunk set per transcript body; the UPPER_SNAKE form of the id replaces -
CASSINI_TX_<UPPER_ID>_PAYLOAD_MIME=<that transcript's payloadRef.mime>
CASSINI_TX_<UPPER_ID>_PAYLOAD_ENCODING=base64url+gzip+utf8json
CASSINI_TX_<UPPER_ID>_PAYLOAD_CHUNK_COUNT=<N>
CASSINI_TX_<UPPER_ID>_PAYLOAD_SHA256=<hex>
CASSINI_TX_<UPPER_ID>_PAYLOAD_RAW_BYTES=<N>
CASSINI_TX_<UPPER_ID>_PAYLOAD_GZIP_BYTES=<N>
CASSINI_TX_<UPPER_ID>_PAYLOAD_000..N=<chunks>
```

Every descriptor above is REQUIRED alongside its chunk set, and every one
duplicates a member of that transcript's `payloadRef`. The manifest is the
record: see
[When a tag and the manifest disagree](#when-a-tag-and-the-manifest-disagree).

`payloadRef.prefix` is authoritative. A consumer MUST use it as written, folding
ASCII case when matching tag names, and MUST NOT re-derive it from the id.
A producer MUST derive it as `CASSINI_TX_` + the id upper-cased with `-`
replaced by `_` + `_PAYLOAD_`, and MUST reject a set of transcript ids whose
derived prefixes collide — not merely one with duplicate ids. See
[Reserved transcript ids](#reserved-transcript-ids).

The media type is per role, not a constant: a word-timed body carries
`application/vnd.cassini.transcript-words+json` and a readable or display body
carries `application/vnd.cassini.transcript-readable+json`.

Each chunk set follows the rules under [Chunk sets](#chunk-sets) and the
encoding under [Payload encoding](#payload-encoding). Bodies are
`cassini.words.v1` JSON, defined in
[`spec/cassini-words-v1.md`](spec/cassini-words-v1.md) with a schema at
[`spec/cassini-words-v1.schema.json`](spec/cassini-words-v1.schema.json); one
schema covers both a v1 file's inline `manifest.transcript` and a v2/v3
chunk-set body, because they are the same document type.

### Reserved transcript ids

A transcript id MUST match `^[a-z0-9][a-z0-9-]{0,31}$`, and MUST be unique
within the file.

`-` is legal and `_` is not. A transcript's tag prefix is built by upper-casing
its id and replacing `-` with `_`, so `raw-asr` and `raw_asr` would both address
`CASSINI_TX_RAW_ASR_PAYLOAD_`: two entries in `transcripts[]`, one chunk set,
one body lost with no error anywhere. Producers MUST reject an id containing
`_`, and MUST reject two ids that map to the same tag prefix even if a future
grammar makes that possible again. A consumer that meets such a pair in an older
file MUST treat as unreadable every entry whose `payloadRef.sha256` does not
match the one body that is there, and MUST NOT serve one body under two ids.

The id is also the provenance map key: an entry with `id: "canary"` resolves to
`provenance.speechToText.canary`.

These ten ids are reserved and producers MUST reject them. They are the
manifest's own top-level member names, held back so that a transcript id can
never read as one of them in a log line, a URL or a tag dump:

```text
payload, format, audio, meeting, integrity, transcript,
provenance, summary, attachments, speakers
```

Ids are lowercase by grammar, so this is an exact-match check, not a case fold.

### Audio integrity

V3 preserves v2's multi-transcript manifest and OpusTag layout. It changes
only the recording identity and integrity policy:

- `CASSINI_FORMAT=org.cassini.portable-meeting/1`
- `CASSINI_PAYLOAD_SCHEMA=https://cassini.local/spec/cassini-portable-meeting-manifest-v1.schema.json`
- `integrity.matchPolicy=exact-opus-audio-v1`
- `integrity.opusAudioSha256=<64 lowercase hex characters>`
- `CASSINI_AUDIO_MATCH_POLICY=exact-opus-audio-v1`
- `CASSINI_AUDIO_OPUS_SHA256=<the same digest>`

The digest covers playback-relevant `OpusHead` fields, every compressed audio
packet in order with packet boundaries, and the normalized playable sample
count. It excludes `OpusTags` and raw Ogg framing, including page layout,
serial numbers, CRCs, and granule positions.
That makes the identity non-circular and stable across metadata-only remuxes:
the manifest can contain its own audio digest without the tag rewrite changing
that digest.

Playable sample count and duration remain required shape fields. The canonical
algorithm validates the Ogg stream, derives packet duration at Opus's 48 kHz
clock, and honors valid end trimming without making muxer-specific granule
normalization part of the digest. The complete byte-level contract is
[`spec/cassini-opus-audio-integrity-v1.md`](spec/cassini-opus-audio-integrity-v1.md).

V3 producers MUST compute this digest without decoding the audio, and MUST
verify it against the file they are about to publish before publishing it.

V3 consumers follow [Trust and integrity](#trust-and-integrity) unchanged: a
policy or a digest they cannot check is `unverified`; a digest or shape
mismatch is `stale-audio`. Neither discards the transcript.

A fresh v3 content-derived meeting id is the literal `mtg_` followed by the full
64 lowercase hex characters of the compressed-audio digest, so
`meeting.id == "mtg_" + integrity.opusAudioSha256`. `CASSINI_MEETING_ID` carries
the same string. A producer whose id comes from elsewhere MAY write any stable
non-empty string instead, and consumers MUST NOT parse a digest back out of an
id. Therefore a metadata-only retag preserves the ID, while re-encoding the same
audible content normally creates a different ID. The operator's catalog/job ID
and its separate whole-file sealed digest are unaffected.

## Writing a file

### Producer requirements

Cassini producers MUST:

- produce valid Ogg Opus audio
- write all required Cassini descriptor tags
- embed a manifest conforming to the v3 schema
- compute `CASSINI_AUDIO_OPUS_SHA256` from the canonical compressed Opus audio
  packet stream defined in
  [`spec/cassini-opus-audio-integrity-v1.md`](spec/cassini-opus-audio-integrity-v1.md)
- ensure summary tags and manifest agree
- re-read the file they just wrote and refuse to ship one whose digest or shape
  fields disagree with its own manifest, per
  [Where the hard check lives](#where-the-hard-check-lives)

Cassini producers SHOULD:

- write compact JSON before compression
- keep only canonical and useful derived data
- avoid embedding large redundant indexes

### What belongs in the file

A portable meeting file SHOULD carry:

- the meeting's identifying and summary fields, in the manifest
- the speaker table, in the manifest
- the canonical word transcript — in v2 and v3 as its own chunk set named by a
  `transcripts[]` entry; in v1 inline under `transcript.items`
- optionally, a readable transcript derived from it, as its own chunk set named
  by a `readableTranscripts[]` entry
- optionally, chapter markers, inline in the manifest's `chapters` array

A portable meeting file SHOULD NOT carry:

- search indexes
- browser build products
- captions, which are mechanically derivable from the canonical transcript

In v2 and v3 the manifest is an index and stays small; the chunk sets it points
at are where the bulk lives. In the published demo the manifest is 2,127 bytes
uncompressed against a 45,837-byte transcript body. A v1 manifest inlines the
transcript instead and is correspondingly large — between 431,614 and 1,708,055
bytes across the shipped v1 corpus.

## Rationale

### Why not use a single binary blob tag only

Because the format should be legible.

The format intentionally requires:

- explicit encoding tags
- explicit integrity tags
- explicit chunk count
- explicit decode hint

That makes the metadata self-describing enough that a curious user can inspect
and decode it without reading Cassini source code first.

### Rejected alternatives

#### ZIP-like `.cassini` package

Rejected as the primary format because it is not directly playable in ordinary
audio players.

#### MP4/M4A with custom payload

Rejected because Cassini already prefers Opus and because Ogg/OpusTags
is easier to inspect casually from the command line.

#### WebM audio file

Rejected because it is less obviously "just an audio file" than `.opus`
for ordinary users.

#### Raw JSON in tags with no compression

Rejected because it creates unnecessary tag bloat and offers no practical
advantage in Cassini's expected size range.

### Why `.meeting` is not a contract

The build pipeline still uses a `.meeting` bundle directory as an intermediate
working form. That directory carries two internal manifest files:

- `cassini.json` — the bundle envelope (`cassini.meeting.v1`)
- `manifest.json` — the artifact manifest (`cassini.meeting-artifact.v1`)

These are **build scratch, not a published format**. The only durable Cassini
deliverable is the `.opus` portable meeting file with its embedded
`org.cassini.portable-meeting/1` manifest. The `.meeting` bundle and its two
manifest schemas exist purely to stage the pack into `.opus`; they are
deliberately not documented as a consumer contract and are scheduled to be
retired once the build/publish flows no longer depend on them. Do not treat the
`.meeting` bundle, `cassini.json`, or the bundle `manifest.json` as a stable
interface.

### Implementation notes kept elsewhere

How the Cassini operator guarantees that a sealed, verified `.opus` actually
exists before anything downstream consumes it is an implementation concern, not
part of this format. It is recorded in
[`design/operator-sealing.md`](design/operator-sealing.md) because the reasoning
transfers to any other producer with the same problem.
