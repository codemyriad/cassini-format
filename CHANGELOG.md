# Changelog

Versions of the format itself, not of this repository. Each one is identified in
a file by its `CASSINI_FORMAT` tag.

## Specification changes that are not format changes

The wire format did not move. These change what the documents say about it, and
what the schemas accept.

### 2026-09-01

* `cassini.words.v1`, the transcript body, is written down for the first time:
  [`spec/cassini-words-v1.md`](spec/cassini-words-v1.md) and
  [`spec/cassini-words-v1.schema.json`](spec/cassini-words-v1.schema.json). One
  schema covers both a v1 file's inline `manifest.transcript` and a v2/v3
  chunk-set body, because they are the same document type. Verified against a
  real file of each.
* **Correction:** items are in speaker-turn order, **not** sorted by `startMs`.
  Across a speaker change `startMs` goes backwards, because overlapping speech
  keeps each speaker's words together. Sorting by time destroys every turn. The
  first draft of the body spec said the opposite and was wrong.
* The v1 manifest schema declares `displayTranscript`. Without it the schema
  rejected all nine shipped v1 files, which is a schema that cannot validate the
  files it describes.
* [`spec/cassini-opus-audio-integrity-v1.md`](spec/cassini-opus-audio-integrity-v1.md)
  defines `finalGranule` and what makes one invalid. Both were used in the
  normative formula and defined nowhere. The same file now cites RFC 6716
  sections 3.1 and 3.2.5 for packet duration and for the frame-count rules that
  make a packet malformed, states the length prefix exactly (marker byte, then
  the length, then the packet, with the length counting the packet only), and
  says milliseconds truncate toward zero. Its one contradiction is gone: the
  final granule is not excluded from the digest, it bounds the playable sample
  count that is hashed.
* A website: [`site/`](site/). It renders these documents rather than copying
  them, ships a real v3 file everything on it is measured from, and publishes
  the whole specification flattened as `/llms-full.txt`.
* `SPEC.md` rewritten and reordered. It is now sorted into the machinery every
  version shares (identify a file, read the comment vector, reassemble a chunk
  set, decide whether to trust it), then the current manifest, then the earlier
  versions, and no section states a v1-only rule without v1 in a heading above
  it. The substantive changes:
  * A chunk set is defined once, over a tag prefix, so the manifest and every
    transcript body are one mechanism instead of a v1 rule plus a v2 special
    case. The index is zero-padded to a *minimum* of three digits, which is what
    the producer has always written.
  * `Implementing this`: the specifications this format inherits, with section
    numbers, and the Ogg page CRC parameters that RFC 3533 leaves out.
  * `Reading the comment vector`: which packet the tags are in, that it spans
    pages, that the separator is the first `=`, that names are
    case-insensitive, and what to do with a repeated name.
  * One integrity rule instead of three, with six named trust states —
    `plain-audio`, `unknown-cassini-format`, `invalid-cassini-metadata`,
    `unverified`, `stale-audio`, `ok`. None of them discards the transcript;
    the hard check moves to the producer, which is where it already was.
  * `Embedded manifest` points at the schema for the file's own `version`
    instead of always at v1, states the value of `kind`, and requires
    `transcripts` rather than a singular `transcript` no v3 file carries.
  * The transcript index, the per-transcript chunk sets and the reserved ids
    move out of the section marked legacy and into the current version, where a
    v3 implementer can find them.
  * base64url is stated as unpadded, and a consumer is required to bound its
    inflate against the declared `RAW_BYTES` before performing it.
  * Transcript ids may not contain `_`, because the tag prefix collapses it and
    one transcript's body is then lost with no error. The reserved list is ten,
    matching the code.
  * `exact-pcm` is no longer an unconditional MUST to run an algorithm nobody
    published. A consumer that cannot reproduce it reports `unverified`.
  * Extensibility, private use under `X_` and `x`, and `payloads`/`CASSINI_PL_`
    reserved for later.
  * The rollout plan moved to
    [`design/rollout-plan-v1.md`](design/rollout-plan-v1.md); it was a CLI
    delivery plan inside a format specification, and it named commands that do
    not exist.
* An errata list, [`ERRATA.md`](ERRATA.md). It now records the other direction:
  rules `SPEC.md` states that the reference readers do not follow yet.
* [`spec/conformance/`](spec/conformance/): 22 vectors, a language-agnostic
  index and a harness, so "does my reader conform" has an answer. Running it
  found three disagreements between the reference implementation and these
  documents, two of them in files this repository's own readers decode fine.

## v3 — `org.cassini.portable-meeting/1` (2026-08-29)

Current producer format. The number is contested: the format freeze written the
day before proposed publishing the renamed format as `<name>/2`, which `/3` now
cuts across. See [freeze item 6](design/format-freeze-2026-08-28.md#6-publish-as-version-2-must).

* Recording identity moves from decoded PCM to the compressed Opus audio:
  `integrity.matchPolicy = exact-opus-audio-v1`, digest in
  `integrity.opusAudioSha256`, byte stream defined in
  [`spec/cassini-opus-audio-integrity-v1.md`](spec/cassini-opus-audio-integrity-v1.md).
* A consumer no longer has to decode the audio to verify identity.
* The digest excludes `OpusTags` and Ogg framing, so it survives a
  metadata-only remux and is not self-referential.
* Manifest and OpusTag layout are unchanged from v2.
* `containerSha256` dropped. `matchPolicy` survives and the freeze proposal
  wants it gone.

## v2 — `org.cassini.portable-meeting/2` (2026-05-12)

Legacy writer format; readers still support it.

* One file can carry several transcripts of the same audio: `transcripts` and
  `readableTranscripts` arrays replace the single `transcript` /
  `readableTranscript` objects.
* Each transcript body moves into its own OpusTag chunk set with its own gzip
  envelope and SHA-256, addressed from the manifest by `payloadRef`. A consumer
  decompresses only the body it displays.
* `provenance.speechToText` and `provenance.readableCleanup` become maps keyed
  by transcript id.
* `CASSINI_TRANSCRIPT_IDS` and `CASSINI_TRANSCRIPT_DEFAULT` make the set
  discoverable from `ffprobe` alone.

## v1 — `org.cassini.portable-meeting/1` (2026-03)

The original: Ogg Opus, one transcript, manifest gzipped and base64url-encoded
across `CASSINI_PAYLOAD_000..N`, identity as a SHA-256 of decoded s16le PCM
(`integrity.matchPolicy = exact-pcm`).
