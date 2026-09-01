#!/usr/bin/env python3
"""Read a Cassini portable meeting with no external tools at all.

Same result as the ffprobe reader, but it walks the Ogg pages and the OpusTags
comment packet itself: standard library, nothing else, about a hundred lines.
Everything it needs lives in the first two packets, so it only ever looks at the
front of the file — the same code reads a meeting over an HTTP Range request
without downloading the audio. A short read raises "truncated before the comment
header ended", which is the signal to ask for more bytes.

    python3 cassini_read_pure.py meeting.opus

SPDX-License-Identifier: CC0-1.0
"""
import base64, binascii, gzip, hashlib, json, struct, sys, zlib

HEAD_BYTES = 1 << 20        # 1 MiB is enough for the metadata of a real meeting


def opus_tags(data):
    """Ogg bytes -> (vendor, {FIELD: value}, bytes_consumed). Names upper-cased.

    Reassemble PACKETS, not pages. An Ogg page holds at most 255 x 255 = 65,025
    bytes, and a comment header carrying a transcript is routinely bigger than
    that, so OpusTags spans several pages. A lacing value below 255 ends a
    packet; a run of 255s means "continues".
    """
    packets, partial, pos = [], b"", 0
    while pos < len(data) and len(packets) < 2:
        if data[pos:pos + 4] != b"OggS":
            raise ValueError(f"not an Ogg stream at byte {pos}")
        nsegs = data[pos + 26]
        lacing = data[pos + 27:pos + 27 + nsegs]
        cur = pos + 27 + nsegs
        pos = cur + sum(lacing)
        if pos > len(data):
            raise ValueError("truncated before the comment header ended")
        for n in lacing:
            partial += data[cur:cur + n]
            cur += n
            if n < 255:
                packets.append(partial)
                partial = b""
    if len(packets) < 2 or packets[0][:8] != b"OpusHead" or packets[1][:8] != b"OpusTags":
        raise ValueError("not an Ogg Opus stream")

    pkt = packets[1]
    vendor_len, = struct.unpack_from("<I", pkt, 8)
    off = 12 + vendor_len
    vendor = pkt[12:off].decode("utf-8", "replace")
    count, = struct.unpack_from("<I", pkt, off)
    off += 4
    tags = {}
    for _ in range(count):
        size, = struct.unpack_from("<I", pkt, off)
        off += 4
        name, _, value = pkt[off:off + size].decode("utf-8").partition("=")
        off += size
        if name.upper() in tags:
            raise ValueError(f"duplicate OpusTags field {name!r}")
        tags[name.upper()] = value
    return vendor, tags, pos


def chunks(t, prefix, count, sha256=None):
    """PREFIX_000..N-1 -> base64url -> gzip -> UTF-8 JSON."""
    missing = [i for i in range(count) if f"{prefix}{i:03d}" not in t]
    if missing:
        raise ValueError(f"{prefix}*: missing chunk {prefix}{missing[0]:03d}")
    b64 = "".join(t[f"{prefix}{i:03d}"] for i in range(count)).rstrip("=")
    # A damaged payload is damaged metadata over valid audio, not a crash:
    # zlib.error is not an OSError, and JSONDecodeError is not a ValueError
    # subclass anybody remembers.
    try:
        body = gzip.decompress(base64.urlsafe_b64decode(b64 + "=" * (-len(b64) % 4)))
    except (binascii.Error, OSError, EOFError, zlib.error) as exc:
        raise ValueError(f"{prefix}*: payload will not decode: {exc}") from None
    got = hashlib.sha256(body).hexdigest()
    if sha256 and got != sha256.lower():
        raise ValueError(f"{prefix}*: sha256 {got} != declared {sha256}")
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{prefix}*: payload is not JSON: {exc}") from None


def read(data):
    """Ogg bytes -> (manifest, words, bytes_used). Manifest None for plain audio."""
    _vendor, t, used = opus_tags(data)
    if not t.get("CASSINI_FORMAT"):
        return None, None, used
    manifest = chunks(t, "CASSINI_PAYLOAD_", int(t["CASSINI_PAYLOAD_CHUNK_COUNT"]),
                      t.get("CASSINI_PAYLOAD_SHA256"))
    entries = manifest.get("transcripts") or []
    if not entries:                                     # v1 keeps the body inline
        return manifest, (manifest.get("transcript") or {}).get("items", []), used
    want = next((e["id"] for e in entries if e.get("default")),
                t.get("CASSINI_TRANSCRIPT_DEFAULT")) or entries[0]["id"]
    ref = next(e for e in entries if e["id"] == want)["payloadRef"]
    body = chunks(t, ref["prefix"], ref["chunkCount"], ref["sha256"])
    return manifest, body["items"], used


if __name__ == "__main__":
    with open(sys.argv[1], "rb") as fh:
        head = fh.read(HEAD_BYTES)              # never reads the audio
        total = fh.seek(0, 2)
    try:
        manifest, words, used = read(head)
    except ValueError as exc:
        sys.exit(f"{sys.argv[1]}: {exc}")
    if manifest is None:
        sys.exit(f"{sys.argv[1]}: plain audio, no Cassini metadata")
    print(f'{manifest["meeting"]["title"]} - {len(words)} words, '
          f'{manifest["meeting"]["durationMs"] / 1000:.0f} s')
    print(f"all of it came from the first {used} of {total} bytes "
          f"({100 * used / total:.2f}%)")
    for w in words[:6]:
        print(f'{w["startMs"]:>8} ms  {w["speaker"]:<10} {w["text"]}')
