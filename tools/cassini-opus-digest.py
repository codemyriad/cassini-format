#!/usr/bin/env python3
"""Compute exact-opus-audio-v1, the Cassini audio digest, from an Ogg Opus file.

Written from spec/cassini-opus-audio-integrity-v1.md alone, with no reference to
the Go implementation, and byte-identical to it. Standard library only: no
ffmpeg, no Opus decoder. Points the spec left open are marked SPEC-GAP.

    python3 tools/cassini-opus-digest.py meeting.opus

Compare the printed sha256 with the file's own CASSINI_AUDIO_OPUS_SHA256 tag.
Equal means the compressed audio is exactly what the metadata was written for.
The digest ignores Ogg framing, so a metadata-only remux does not change it.

SPDX-License-Identifier: CC0-1.0
"""
import hashlib, json, struct, sys

# SPEC-GAP: the spec says the parser "validates the Ogg structure and CRC" but
# never names the CRC parameters. From the Ogg container spec: poly 0x04c11db7,
# init 0, no reflection, no final xor. (Not zlib's crc32, which is reflected.)
CRC = []
for _i in range(256):
    _r = _i << 24
    for _ in range(8):
        _r = ((_r << 1) ^ 0x04c11db7) & 0xFFFFFFFF if _r & 0x80000000 else (_r << 1) & 0xFFFFFFFF
    CRC.append(_r)


def ogg_crc(buf):
    crc = 0
    for b in buf:
        crc = ((crc << 8) & 0xFFFFFFFF) ^ CRC[((crc >> 24) & 0xFF) ^ b]
    return crc


def packet_samples(pkt):
    """Samples at Opus's fixed 48 kHz clock, from the TOC byte alone.

    RFC 6716 section 3.1 for the TOC byte itself, section 3.2.5 for the
    frame-count rules the integrity spec makes normative: a code-3 packet
    carries a frame-count byte, the count is never zero, and no packet's audio
    duration exceeds 120 ms. A packet that breaks one of those is malformed and
    the file is rejected, not given a duration of zero.
    """
    if not pkt:
        raise ValueError("empty Opus packet")
    toc = pkt[0]
    if toc & 0x80:                                  # CELT-only: 2.5/5/10/20 ms
        spf = (48000 << ((toc >> 3) & 0x03)) // 400
    elif (toc & 0x60) == 0x60:                      # Hybrid: 10 or 20 ms
        spf = 48000 // 50 if toc & 0x08 else 48000 // 100
    else:                                           # SILK: 10/20/40/60 ms
        code = (toc >> 3) & 0x03
        spf = 48000 * 60 // 1000 if code == 3 else (48000 << code) // 100
    frame_code = toc & 0x03
    if frame_code == 3:
        if len(pkt) < 2:
            raise ValueError("code-3 Opus packet has no frame-count byte")
        frames = pkt[1] & 0x3F
        if frames == 0:
            raise ValueError("code-3 Opus packet declares zero frames")
    else:
        frames = 1 if frame_code == 0 else 2
    total = spf * frames
    if total > 48000 * 120 // 1000:
        raise ValueError(f"Opus packet is {total} samples, over the 120 ms limit")
    return total


def compute(path):
    data = open(path, "rb").read()
    h = hashlib.sha256()
    h.update(b"org.cassini.opus-packets/1\x00")          # 1. domain separator

    pos, partial = 0, b""
    index = audio_packets = decoded = 0
    serial = pre_skip = channels = final_granule = None
    expect_seq = 0
    while pos < len(data):
        if data[pos:pos + 4] != b"OggS" or data[pos + 4] != 0:
            raise ValueError(f"bad Ogg page header at byte {pos}")
        flags, granule, page_serial, seq = struct.unpack_from("<BQII", data, pos + 5)
        nsegs = data[pos + 26]
        lacing = data[pos + 27:pos + 27 + nsegs]
        body = pos + 27 + nsegs
        payload = data[body:body + sum(lacing)]
        if len(payload) != sum(lacing):
            raise ValueError("truncated Ogg page")

        header = bytearray(data[pos:body])
        want = struct.unpack_from("<I", header, 22)[0]
        header[22:26] = b"\0\0\0\0"
        if ogg_crc(bytes(header) + payload) != want:
            raise ValueError(f"Ogg CRC mismatch on page {seq}")

        if serial is None:
            serial = page_serial
            if not flags & 0x02:
                raise ValueError("first page is not marked beginning-of-stream")
        elif page_serial != serial:
            raise ValueError("multiplexed or chained Ogg stream")
        if seq != expect_seq:
            raise ValueError(f"page sequence gap: expected {expect_seq}, got {seq}")
        if bool(flags & 0x01) != bool(partial):
            raise ValueError(f"invalid continuation flag on page {seq}")
        expect_seq += 1

        cur = 0
        for n in lacing:
            partial += payload[cur:cur + n]
            cur += n
            if n == 255:
                continue                                 # packet continues
            if index == 0:                               # 2. OpusHead
                if partial[:8] != b"OpusHead" or partial[8] != 1:
                    raise ValueError("first packet is not an Opus v1 identification header")
                channels, pre_skip = partial[9], struct.unpack_from("<H", partial, 10)[0]
                canon = bytearray(partial)
                canon[12:16] = b"\0\0\0\0"               # zero the input sample rate
                h.update(b"H" + struct.pack("<Q", len(canon)) + bytes(canon))
            elif index == 1:                             # OpusTags: excluded
                if partial[:8] != b"OpusTags":
                    raise ValueError("second packet is not a comment header")
            else:                                        # 3. audio packets
                decoded += packet_samples(partial)
                h.update(b"A" + struct.pack("<Q", len(partial)) + partial)
                audio_packets += 1
            index += 1
            partial = b""
        if flags & 0x04:
            final_granule = granule
        pos = body + len(payload)

    if partial:
        raise ValueError("stream ends inside an unterminated packet")
    if final_granule is None:
        raise ValueError("missing end-of-stream page")
    if final_granule > 0x7FFFFFFFFFFFFFFF:           # negative as a signed 64-bit
        raise ValueError(f"final granule {final_granule - (1 << 64)} is negative")
    if final_granule < pre_skip:
        raise ValueError(f"final granule {final_granule} is below pre-skip {pre_skip}")

    # Sum packet durations, subtract pre-skip, clamp to the muxer's own view.
    sample_count = min(decoded - pre_skip, final_granule - pre_skip)
    h.update(b"E" + struct.pack("<QQ", audio_packets, sample_count))   # 4. trailer
    # Milliseconds truncate toward zero: the demo file is exactly 239713.5 ms.
    return {"sha256": h.hexdigest(), "sampleRate": 48000, "channels": channels,
            "sampleCount": sample_count, "durationMs": sample_count * 1000 // 48000,
            "packetCount": audio_packets, "preSkip": pre_skip}


if __name__ == "__main__":
    try:
        print(json.dumps(compute(sys.argv[1]), indent=2))
    except ValueError as exc:
        sys.exit(f"{sys.argv[1]}: {exc}")
