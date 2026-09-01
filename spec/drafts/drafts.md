# The draft formats

See [README.md](README.md). Kept verbatim as they were written.

<!-- spec:part v2 -->

## Reading v2

`org.cassini.portable-meeting/2`, dated 2026-05-12. No producer writes it;
reader support is retained, and every rule in it is still live in v3.

### What v2 changes

v2 lets a single `.opus` file carry **multiple transcripts of the same audio**
(e.g. parakeet + canary, or raw ASR + human-corrected) so the viewer can switch
or compare without producing duplicate files. The audio profile, integrity
rules, OpusTag transport, and decode steps from v1 stay the same. The only
structural change is in how transcript bodies are addressed.

### File identification (v2)

A v2 file MUST set:

- `CASSINI_FORMAT=org.cassini.portable-meeting/2`
- `CASSINI_PAYLOAD_SCHEMA=https://cassini.local/spec/cassini-portable-meeting-manifest-v2.schema.json`

All other v1 descriptor tags still apply.

### Manifest shape (v2)

The decompressed `CASSINI_PAYLOAD_*` body MUST conform to
[`spec/cassini-portable-meeting-manifest-v2.schema.json`](spec/cassini-portable-meeting-manifest-v2.schema.json).
Notable differences from v1:

| v1 | v2 |
|---|---|
| `transcript: object` (single, required) | `transcripts: array` (1..N), required |
| `readableTranscript: object` (optional, single) | `readableTranscripts: array` (0..N), optional |
| `provenance.speechToText: ProcessingStep` | `provenance.speechToText: map<transcriptId, ProcessingStep>` |
| `provenance.readableCleanup: ProcessingStep` | `provenance.readableCleanup: map<transcriptId, ProcessingStep>` |
| transcript body inlined under `transcript.items` | each transcript body lives in its own OpusTag chunk set; the manifest entry holds a `payloadRef` |

The entry shape and the tag layout are unchanged in v3 and are defined once,
under [Transcripts and their chunk sets](#transcripts-and-their-chunk-sets).

### Producer rules (v2)

Producers writing v2 files MUST:

- Flag at most one `default: true` entry per slot — one across the word-timed
  roles `raw-asr`, `human-corrected` and `translation`, one across
  `readable-cleanup`, one across `display`. Flagging none is legal; consumers
  fall back to array order.
- Reject any transcript id that is reserved or ill-formed; see
  [Reserved transcript ids](#reserved-transcript-ids).
- Compute `payloadRef.sha256` against the decompressed body JSON bytes
  (not the gzip or base64url forms).
- Include a `provenance.speechToText.<id>` entry for every transcript entry
  with `role: raw-asr`; same shape for cleanup-role entries under
  `readableCleanup`.

Producers MUST NOT write a top-level `transcript` field in v2 files. v1
consumers reading a v2 file SHOULD detect `version: 2` and surface a
"newer format" message rather than guessing at the index shape.

### Consumer rules (v2)

A v2 consumer follows [Reading a file](#reading-a-file) unchanged. Two things
are specific to v2 and v3:

- the main payload is an index, not a transcript: reading it yields the meeting,
  the speakers and the list of transcripts, and each body costs a second decode;
- a v1 file presents the same way if a consumer synthesizes the index — one
  `raw-asr` entry from `transcript`, and where present a `readable-cleanup`
  entry from `readableTranscript` and a `display` entry from `displayTranscript`,
  each carrying its body inline rather than behind a `payloadRef`. One code path
  then reads all three versions.

A synthesized entry is a reader's own construct and is not schema-valid:
`transcriptEntry` requires a `payloadRef` and there is none.

<!-- spec:part v1 -->

## Reading v1

`org.cassini.portable-meeting/1` is the original version, dated 2026-03-11. No
producer writes it. Nine shipped files carry it and consumers MUST read them.

A v1 file uses the same container, the same two metadata layers, the same chunk
sets and the same payload encoding as v3. Three things differ.

**The transcript is inline.** A v1 manifest has no `transcripts` array and no
`CASSINI_TX_<UPPER_ID>_PAYLOAD_` chunk sets. Its one word-timed transcript is
the top-level `transcript` object, whose body is the same `cassini.words.v1`
document a v3 chunk set decodes to. Beside it, both optional and both present in
every shipped file, sit `readableTranscript` and `displayTranscript`. A consumer
that synthesizes a one-entry index from them reads all three versions on one
code path; see [Consumer rules (v2)](#consumer-rules-v2).

**Provenance is single objects, not maps.** `provenance.speechToText`,
`readableCleanup` and `displayTranscript` are each one processing step, because
a v1 file has exactly one transcript. `meetingSummary`, `attribution` and
`wordTimings` were added at v2 and are absent here. A reader that unmarshals a
v2 or v3 map into the v1 shape succeeds silently and yields empty values, which
is the mistake to watch for.

**Integrity is `exact-pcm`**, described below.

The descriptor tags are the v1 ones:
`CASSINI_FORMAT=org.cassini.portable-meeting/1`, `CASSINI_PAYLOAD_SCHEMA`
naming the v1 schema, and `CASSINI_AUDIO_PCM_FORMAT`, `CASSINI_AUDIO_PCM_SHA256`
and `CASSINI_AUDIO_MATCH_POLICY=exact-pcm` in place of the two
`exact-opus-audio-v1` tags. `CASSINI_TRANSCRIPT_IDS` and
`CASSINI_TRANSCRIPT_DEFAULT` do not appear.

Because the transcript is inline, a v1 manifest is large: between 431,614 and
1,708,055 bytes uncompressed across the shipped corpus, against 2,127 for the v3
demo. A consumer that wants only the title and the speaker list still pays for
the whole document, which is the cost v2 removed.

### Legacy integrity: exact-pcm

V1 and v2 files carry `CASSINI_AUDIO_PCM_FORMAT=s16le`,
`CASSINI_AUDIO_PCM_SHA256` and `CASSINI_AUDIO_MATCH_POLICY=exact-pcm`, and
`integrity.pcmSha256` / `integrity.pcmFormat` in the manifest, in place of the
compressed-audio digest.

The byte stream that digest covers is **not specified**, and this document does
not specify it retrospectively. It was computed over decoded PCM, and decoding
Opus to PCM is decoder-dependent: two decoders in one ffmpeg build produce
different bytes for the same file. That is why v3 exists.

A consumer MAY verify a v1 or v2 file's `pcmSha256` if it happens to reproduce
the producer's decode. A consumer that cannot MUST report `unverified` — not
`stale-audio`, and not `ok`. The shape fields are still checkable and SHOULD be
checked; note that v1 files were written with the pre-encode source's
`sampleCount`, so every shipped v1 file disagrees with its own audio by exactly
the 312-sample Opus pre-skip, and a consumer that treats that as a mismatch
reports `stale-audio` on a file that is entirely intact.

Writers MUST NOT reinterpret an older file's PCM digest as a compressed-audio
digest, and MUST NOT relabel an old file's `CASSINI_AUDIO_MATCH_POLICY` while
retagging it.
