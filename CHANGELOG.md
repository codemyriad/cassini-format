# Changelog

Versions of the format itself, not of this repository. Each one is identified in
a file by its `CASSINI_FORMAT` tag.

## v3 — `org.cassini.portable-meeting/3` (2026-08-29)

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
