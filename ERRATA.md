# Errata

Date: 2026-09-02

Status: every entry checked against the reference producer's source and against a
file on disk

Rules [`SPEC.md`](SPEC.md) states that the reference implementations do not yet
follow, plus a few facts about real files worth knowing before you write a
reader. Each entry was checked against the producer's source and against a file
on disk.

## The six trust states are not the names the readers print

[Trust and integrity](SPEC.md#trust-and-integrity) requires every read to end in
one of `plain-audio`, `unknown-cassini-format`, `invalid-cassini-metadata`,
`unverified`, `stale-audio` or `ok`, and requires the state to be visible to
whoever called the reader. Three gaps:

* `cassini inspect` resolves all six and prints the fourth as
  `integrity-unverified`. Same state, different spelling.
* The browser viewer never verifies the audio: it renders the transcript from a
  byte-range request before the audio has been downloaded. It says
  **unverified** where it presents the metadata, which is what makes that
  conforming.
* `cassini inspect` calls the whole file `invalid-cassini-metadata` when a
  transcript body is missing a chunk. [Resolving a
  transcript](SPEC.md#resolving-a-transcript) makes that transcript
  unavailable and leaves the file's state alone. Conformance vector 006 is
  that case; it is the one vector the Go reader fails.

## Nothing bounds the decompression

[Payload encoding](SPEC.md#payload-encoding) requires a consumer to stop
inflating as soon as the output exceeds the declared `RAW_BYTES`. No reader here
does: all of them inflate first and check the size afterwards. On a
2,172,012-byte file whose chunks declare 203,932 gzip bytes that inflate to
209,715,277 against `CASSINI_PAYLOAD_RAW_BYTES=42`, Go peaks at 550 MB resident,
Python at 430 MB, and `tools/cassini-read.js` at 1.14 GB and returns success. In
a browser tab that is a crash on a file that fits in an email.

## Padding: written unpadded, and the Go reader refuses it

The producer writes unpadded (`base64.RawURLEncoding`), which is what the
document requires. The document also requires a consumer to accept padded input,
and `cassini inspect --transcript` fails on conformance vector
`004-padded-base64url-v1` with `illegal base64 data at input byte 762`.

Two readers also compute the padding from the length before stripping
whitespace, so a chunk value containing a newline decodes on some inputs and not
on others. Strip whitespace first, then pad.

Fixed in the reference implementation by
[gocassini#230](https://github.com/codemyriad/gocassini/pull/230), not yet merged.

## Transcript ids: the producer still accepts `_`

The schemas match the document: `^[a-z0-9][a-z0-9-]{0,31}$`. The producer's own
`transcriptIDRE` does not, and `sanitizeTranscriptID` deliberately preserves
`_`. Nothing checks that two ids derive the same tag prefix either, so `raw-asr`
and `raw_asr` are accepted together, one chunk set is written, and one
transcript's body is gone with no error anywhere.

No file uses `_`. `CASSINI_TRANSCRIPT_IDS` across every v2 and v3 file on this
machine is `raw-asr`, and only ever `raw-asr`.

## The default transcript is resolved from the tag, not the manifest

[Resolving a transcript](SPEC.md#resolving-a-transcript) makes the manifest the
list and the manifest the resolver, with `CASSINI_TRANSCRIPT_DEFAULT` as a copy.
`ExtractMeeting` preferred the tag; `tools/cassini-read.js` did too and now
resolves from the manifest, warning on a disagreement.
`tools/cassini-extract.py` already preferred the manifest flag. The browser
viewer ignores the tag. On a file where the two disagree, readers still show the
user a different transcript. Every shipped file has them agreeing, so nothing is
visibly wrong yet.

Fixed in the reference implementation by
[gocassini#230](https://github.com/codemyriad/gocassini/pull/230), not yet merged.

## The per-transcript chunk count is taken from the tag

The same rule, second instance. Conformance vectors `007` and `008` put
`payloadRef.chunkCount` and `CASSINI_TX_<ID>_PAYLOAD_CHUNK_COUNT` in
disagreement: the Go reader believes the tag and fails with `unexpected EOF`,
the Python and JavaScript readers believe the manifest and decode all 900 words.
The manifest is the record.

Fixed in the reference implementation by
[gocassini#230](https://github.com/codemyriad/gocassini/pull/230), not yet merged.

## `cassini inspect` reports `cassini=ok` on files it cannot decode

`words=` is the *declared* `wordCount` out of the manifest index rather than a
count of anything decoded. Only `--transcript` discovers the body is
unreachable, and even that exits 0.

It also sums word counts across alternative transcripts, so a three-word meeting
carrying two three-word transcripts reports six. Conformance vector `016` is the
minimal reproduction.

Fixed in the reference implementation by
[gocassini#230](https://github.com/codemyriad/gocassini/pull/230), not yet merged.

## Two things about transcript bodies in real files

`language` is written as `""` by the JavaScript repacker in the reference tree,
and omitted by the Go producer. The body format says to treat both as "nobody
said"; a reader that rejects the empty string fails on real files.

No shipped file carries a derived transcript. The reference producer's pack
input has no way to set `sourceTranscriptId`, and its validator rejects a
derived entry without one, so the `readableTranscripts` path is unreachable
today. The shape is specified; nothing exercises it yet.

## Nothing records which program wrote the file

The producer sets `ENCODER=Cassini`; ffmpeg's Ogg muxer replaces the value with
its own, so a real file carries `encoder=Lavf62.3.100`. The tag survives, the
information does not, and that is the fact you need to decide whether a file is
worth reprocessing.

## Tag order, and a risk we accept

The producer sorts tags with `sort.Strings`. ASCII order puts
`CASSINI_PAYLOAD_000` ahead of `CASSINI_PAYLOAD_CHUNK_COUNT`, because `0` sorts
before `C`, so the payload is written before the descriptors that explain it.

[RFC 7845 §5.2](https://www.rfc-editor.org/rfc/rfc7845#section-5.2) lets an
implementation "ignore individual comments that are not fully contained within
the first 61,440 octets of the comment header". A long recording exceeds that:

| file | OpusTags packet | comments past 61,440 |
|---|---|---|
| a 4-minute meeting | 14,376 B | none |
| a 17-minute recording | 84,527 B | 23 of 48 |
| the largest v1 sample | 307,370 B | 77 of 102 |

**In practice nothing truncates.** Tested against the 307 KB file: `ffmpeg -c
copy`, an `.opus` to `.ogg` remux, and a mutagen round-trip each preserve all
102 comments, `CASSINI_PAYLOAD_CHUNK_COUNT` and `CASSINI_PAYLOAD_SHA256`
included. These files are played, not edited, so the exposure is theoretical and
it is accepted.

Worth knowing rather than worth fixing. A new producer may as well write
descriptors before chunk tags, since it costs nothing (the descriptor block is
1,388 bytes, two percent of the window), but no existing file is in danger and
nothing needs repacking.
