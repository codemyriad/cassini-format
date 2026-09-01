# Cassini compressed Opus audio integrity v1

Portable meeting manifest v3 identifies its recording with
`integrity.matchPolicy = "exact-opus-audio-v1"` and a lowercase hexadecimal
SHA-256 in `integrity.opusAudioSha256`.

The digest covers the compressed Opus audio essence, not decoded PCM and not
the complete `.opus` file. Whole-file hashing cannot be embedded in the same
file without becoming self-referential: writing the digest changes OpusTags,
which changes the whole-file digest. The operator may still keep a separate
whole-file delivery digest outside the recording.

## Canonical byte stream

Hash these byte strings in order:

1. The ASCII domain separator `org.cassini.opus-packets/1`, followed by one
   zero byte.
2. The first logical packet (`OpusHead`) after validating it. Set bytes 12–15,
   the informational original input sample rate, to zero. Emit exactly: the
   single ASCII byte `H`, then the packet's length in bytes as an unsigned
   little-endian 64-bit integer, then the packet bytes. The length counts the
   packet only, not the marker.
3. Every compressed audio packet in order, each as the single ASCII byte `A`,
   then that packet's length as an unsigned little-endian 64-bit integer, then
   the packet bytes.
4. A 17-byte trailer: byte `E`, the audio packet count as an unsigned
   little-endian 64-bit integer, and the normalized playable sample count as a
   second unsigned little-endian 64-bit integer.

The second logical packet (`OpusTags`) is excluded. So are Ogg page boundaries,
serial number, sequence number, lacing, CRC, and every granule position except
the final one, which is not hashed directly but bounds the playable sample count
that is. FFmpeg can normalize granule positions during a metadata-only Ogg
stream copy even when OpusHead, every compressed packet, and decoded output are
unchanged. The parser still validates the Ogg structure and CRC before
accepting a stream.

Packet lengths preserve packet boundaries. OpusHead keeps playback-relevant
values including channels, pre-skip, output gain, channel mapping family, and
mapping table.

`finalGranule` is the granule position carried in the header of the last page of
the logical stream. For Ogg Opus that is a count of 48 kHz samples measured from
the start of the decoded output *including* the pre-skip, as defined in
[RFC 7845 §4](https://www.rfc-editor.org/rfc/rfc7845#section-4). `preSkip` is
the pre-skip field of `OpusHead`, at byte offset 10, unsigned little-endian
16-bit.

A final granule is **invalid** when, read as a signed 64-bit integer, it is
negative, or when it is smaller than `preSkip`, since that would describe a
stream with no playable output at all. The all-ones value `-1`, which elsewhere
means "no packet completes on this page", is negative and so is invalid here
too: a last page carrying audio never needs it.

The parser derives each packet's duration from its TOC byte exactly as
[RFC 6716 section 3.1](https://www.rfc-editor.org/rfc/rfc6716#section-3.1)
defines it, at Opus's fixed 48 kHz output clock. It also applies the
frame-count rules of
[RFC 6716 section 3.2.5](https://www.rfc-editor.org/rfc/rfc6716#section-3.2.5):
a code-3 packet MUST carry a frame-count byte, that count MUST NOT be zero, and
a packet's audio duration MUST NOT exceed 120 ms. A packet that violates any of
those is malformed, and the file MUST be rejected rather than the packet
assigned a duration of zero.

The parser sums those durations, subtracts pre-skip, and clamps the result to
`finalGranule - preSkip` when the latter is smaller. This normalized playable
sample count is included in the digest. It keeps a real end trim
identity-relevant while tolerating muxer granules beyond the compressed packet
timeline. Manifest shape fields repeat the same count and its derived duration
even though the digest intentionally ignores raw Ogg framing.

Duration in milliseconds is `sampleCount * 1000 / 48000` in integer arithmetic,
truncated toward zero. A recording of 11506248 samples is 239713 ms, not 239714.

This profile accepts one non-chained Ogg logical stream containing one or two
Opus channels. It rejects malformed headers, malformed Opus packets, CRC
failures, sequence gaps, invalid continuation, multiplexed or chained streams,
truncated packets, missing EOS, and invalid final granules.

Metadata-only remuxes must preserve the digest. Re-encoding audio normally
changes it even when the result sounds equivalent; fresh v3 meeting IDs derive
from this digest for the same reason.
