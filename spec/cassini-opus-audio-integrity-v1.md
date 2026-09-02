# The audio digest: `exact-opus-audio-v1`

Date: 2026-09-02

Status: published

A portable meeting identifies its recording with
`integrity.matchPolicy = "exact-opus-audio-v1"` and a lowercase hex SHA-256 in
`integrity.opusAudioSha256`. This document is the byte rule behind that digest.

It hashes the compressed Opus packets, not decoded PCM and not the whole file.
Decoded PCM is not bit-exact across decoders, so a digest over it depends on
which library you linked. A whole-file digest cannot live inside the file it
covers: writing it changes the tags, which changes the digest. Hashing the
packets and excluding the tags makes the digest stable across any rewrite that
leaves the audio alone.

## The byte stream

Hash these in order:

1. The ASCII string `org.cassini.opus-packets/1`, then one zero byte.
2. The `OpusHead` packet, with bytes 12–15 (the informational input sample
   rate) set to zero. Emit `H`, then the packet length as an unsigned
   little-endian 64-bit integer, then the packet bytes.
3. Every audio packet in stream order. For each, emit `A`, then its length as
   an unsigned little-endian 64-bit integer, then the packet bytes.
4. A trailer: `E`, the audio packet count as an unsigned little-endian 64-bit
   integer, then the playable sample count as another.

Each length counts the packet only, not the marker byte.

Excluded: the `OpusTags` packet, and all Ogg framing. Page boundaries, serial
number, sequence numbers, lacing, CRCs and granule positions do not enter the
hash. The final granule bounds the sample count, but is not hashed itself,
because a metadata-only remux can normalise it while leaving every packet
unchanged.

## The playable sample count

`preSkip` is the `OpusHead` field at bytes 10–11, unsigned little-endian 16-bit.

`finalGranule` is the granule position of the last page of the stream: a count
of 48 kHz samples from the start of decoded output *including* pre-skip, per
[RFC 7845 §4](https://www.rfc-editor.org/rfc/rfc7845#section-4).

Each packet's duration comes from its TOC byte as
[RFC 6716 §3.1](https://www.rfc-editor.org/rfc/rfc6716#section-3.1) defines,
in samples at 48 kHz. The frame-count rules of
[§3.2.5](https://www.rfc-editor.org/rfc/rfc6716#section-3.2.5) apply: a code-3
packet MUST carry a frame count, that count MUST NOT be zero, and a packet MUST
NOT exceed 120 ms. A packet that breaks any of those makes the file invalid.

The playable sample count is the sum of packet durations, minus `preSkip`,
clamped to `finalGranule − preSkip` when that is smaller. The clamp is what lets
a real end trim change the identity while a muxer's granule quirk does not.

Duration in milliseconds is `sampleCount × 1000 / 48000` in integer
arithmetic, truncated. 11,506,248 samples is 239,713 ms, not 239,714.

## What is rejected

The parser accepts one non-chained Ogg logical stream with one or two Opus
channels. It rejects a malformed `OpusHead`, a malformed packet, a CRC failure,
a sequence gap, an invalid continuation, a multiplexed or chained stream, a
truncated packet, a missing end-of-stream flag, and an invalid final granule.

A final granule is invalid when, read as signed 64-bit, it is negative, or when
it is smaller than `preSkip`. The all-ones value that elsewhere means "no packet
ends on this page" is negative and therefore invalid here: a last page carrying
audio never needs it.

## The Ogg page CRC

RFC 3533 names the polynomial and stops, and the rest is not the common
default. Every Cassini file uses:

| Parameter | Value |
|---|---|
| polynomial | `0x04c11db7` |
| initial value | `0` |
| input reflection | none |
| output reflection | none |
| final XOR | none |
| covers | the whole page, with the four CRC bytes set to zero |

This is not the CRC-32 that `zlib.crc32` and most standard libraries give you,
which is reflected with initial value `0xFFFFFFFF` and a final XOR. To check an
implementation: on the first page of the published demo file the stored CRC is
`0x530297d0`. These parameters reproduce it; `zlib.crc32` returns `0x753f3847`.

## Consequences

A metadata-only remux preserves the digest. Re-encoding changes it, even when
the result sounds identical. The reference producer derives `meeting.id` from
this digest, so a tag rewrite keeps a meeting's identity and a re-encode gives it
a new one.
