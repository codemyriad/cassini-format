#!/usr/bin/env python3
"""A complete Cassini producer in pure Python, standard library only.

    cassini-pack.py AUDIO.opus TRANSCRIPT.json OUT.opus \\
        --title "Weekly Sync" --created-at 2026-04-15T09:12:00Z

Takes an Ogg Opus file and a word-timed transcript JSON — either a flat
{"speakers": [...], "items": [{speaker,startMs,endMs,text}]} or the segmented
{"speakers": [...], "segments": [{speaker, words: [...]}]}.

Writes word entries without an origin role. Cassini builds that still require
that label need https://github.com/codemyriad/gocassini/pull/276 before reading
this output. See design/format-simplification-2026-09-07.md for compatibility.

No ffmpeg: it rewrites only the OpusTags packet and re-paginates, copying every
compressed audio page verbatim and patching just the sequence number and CRC.
exact-opus-audio-v1 excludes OpusTags and all Ogg framing, so the digest is
provably unchanged by tagging — unlike the reference Go producer there is no
hash / retag / re-hash fix-point loop to converge. Written from SPEC.md and
spec/cassini-opus-audio-integrity-v1.md alone; the output passes the JSON
Schema, the reference extractor and cassini-opus-digest.py.

SPDX-License-Identifier: CC0-1.0
"""
import argparse, base64, gzip, hashlib, json, re, struct, sys

CHUNK_CHARS = 4096                  # base64url characters per CASSINI_*_nnn tag
VENDOR = "cassini-pack.py"
DESCRIPTION = ("Cassini portable meeting file. Decode CASSINI_PAYLOAD_*: "
               "base64url -> gzip -> UTF-8 JSON.")
DECODE_HINT = ("Concatenate CASSINI_PAYLOAD_000..N for the manifest; for a transcript "
               "body concatenate CASSINI_TX_<ID>_PAYLOAD_000..N. Each chunk set: "
               "base64url decode, gzip decompress, parse UTF-8 JSON.")
# Ids that would collide with a descriptor tag name.
RESERVED_IDS = {"payload", "format", "audio", "meeting", "integrity", "transcript",
                "provenance", "summary", "attachments", "speakers"}

CRC = []                            # poly 0x04c11db7, init 0, no reflection
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


def read_pages(data):
    pos = 0
    while pos < len(data):
        if data[pos:pos + 4] != b"OggS":
            raise ValueError(f"bad Ogg capture pattern at byte {pos}")
        nsegs = data[pos + 26]
        lacing = data[pos + 27:pos + 27 + nsegs]
        body = pos + 27 + nsegs
        yield {"header": data[pos:pos + 27], "lacing": lacing,
               "payload": data[body:body + sum(lacing)],
               "granule": struct.unpack_from("<Q", data, pos + 6)[0]}
        pos = body + sum(lacing)


def parse(data):
    """Split the stream into OpusHead, the audio packets, and the audio pages."""
    head, partial, index, serial = None, b"", 0, None
    audio, audio_pages = [], []
    for page in read_pages(data):
        if serial is None:
            serial = struct.unpack_from("<I", page["header"], 14)[0]
        elif struct.unpack_from("<I", page["header"], 14)[0] != serial:
            raise ValueError("multiplexed or chained Ogg stream")
        cur = 0
        for n in page["lacing"]:
            partial += page["payload"][cur:cur + n]
            cur += n
            if n == 255:
                continue                        # a 255 lacing value means "continues"
            if index == 0:
                head = partial
            elif index > 1:                     # index 1 is OpusTags: discarded
                audio.append(partial)
            index += 1
            partial = b""
        # RFC 7845 puts OpusTags alone on its own page(s), so every page after
        # the one that completes it belongs to the audio.
        if index > 2:
            audio_pages.append(page)
    if head is None or head[:8] != b"OpusHead" or len(head) < 19 or head[8] != 1:
        raise ValueError("not an Ogg Opus stream")
    return head, audio, audio_pages, serial


def packet_samples(pkt):
    """Samples at 48 kHz from the TOC byte: RFC 6716 3.1, frame count 3.2.5.
    A code-3 packet with no frame count, a zero frame count or more than
    120 ms is malformed, and the file is refused rather than given zero."""
    if not pkt:
        raise ValueError("empty Opus packet")
    toc = pkt[0]
    if toc & 0x80:
        spf = (48000 << ((toc >> 3) & 0x03)) // 400
    elif (toc & 0x60) == 0x60:
        spf = 48000 // 50 if toc & 0x08 else 48000 // 100
    else:
        code = (toc >> 3) & 0x03
        spf = 48000 * 60 // 1000 if code == 3 else (48000 << code) // 100
    if toc & 0x03 == 3:
        if len(pkt) < 2:
            raise ValueError("code-3 Opus packet has no frame-count byte")
        frames = pkt[1] & 0x3F
        if frames == 0:
            raise ValueError("code-3 Opus packet declares zero frames")
    else:
        frames = 1 if toc & 0x03 == 0 else 2
    total = spf * frames
    if total > 48000 * 120 // 1000:
        raise ValueError(f"Opus packet is {total} samples, over the 120 ms limit")
    return total


def audio_digest(head, audio, final_granule):
    """exact-opus-audio-v1: hashes the compressed essence, not the file."""
    h = hashlib.sha256()
    h.update(b"org.cassini.opus-packets/1\x00")
    canon = bytearray(head)
    canon[12:16] = b"\0\0\0\0"                  # informational input rate: zeroed
    h.update(b"H" + struct.pack("<Q", len(canon)) + bytes(canon))
    decoded = 0
    for pkt in audio:
        decoded += packet_samples(pkt)
        h.update(b"A" + struct.pack("<Q", len(pkt)) + pkt)
    pre_skip = struct.unpack_from("<H", head, 10)[0]
    if decoded < pre_skip or final_granule < pre_skip:
        raise ValueError("the stream is shorter than its own pre-skip")
    samples = min(decoded - pre_skip, final_granule - pre_skip)
    h.update(b"E" + struct.pack("<QQ", len(audio), samples))
    return h.hexdigest(), samples


def build_tags_packet(vendor, comments):     # a Vorbis comment list, OpusTags layout
    out = bytearray(b"OpusTags")
    v = vendor.encode("utf-8")
    out += struct.pack("<I", len(v)) + v
    out += struct.pack("<I", len(comments))
    for name, value in comments:
        field = f"{name}={value}".encode("utf-8")
        out += struct.pack("<I", len(field)) + field
    return bytes(out)


def lace(n):                                 # 255s, then a remainder that ends the packet
    return bytes([255] * (n // 255) + [n % 255])


def make_page(serial, seq, flags, granule, lacing, payload):
    page = bytearray(b"OggS\0") + bytes([flags]) + struct.pack("<QIII", granule, serial, seq, 0)
    page += bytes([len(lacing)]) + lacing + payload
    struct.pack_into("<I", page, 22, ogg_crc(bytes(page)))
    return bytes(page)


def encode_payload(obj):                     # JSON -> gzip -> base64url -> chunks
    raw = json.dumps(obj, separators=(",", ":")).encode("utf-8")
    gz = gzip.compress(raw, mtime=0)                        # mtime=0: reproducible
    b64 = base64.urlsafe_b64encode(gz).decode().rstrip("=")  # UNPADDED, like Go's
    chunks = [b64[i:i + CHUNK_CHARS] for i in range(0, len(b64), CHUNK_CHARS)]
    return raw, gz, chunks, hashlib.sha256(raw).hexdigest()  # sha256 of the JSON


def chunk_tags(prefix, mime, raw, gz, chunks, sha):
    tags = [(prefix + "MIME", mime),
            (prefix + "ENCODING", "base64url+gzip+utf8json"),
            (prefix + "CHUNK_COUNT", str(len(chunks))),
            (prefix + "SHA256", sha),
            (prefix + "RAW_BYTES", str(len(raw))),
            (prefix + "GZIP_BYTES", str(len(gz)))]
    return tags + [(f"{prefix}{i:03d}", c) for i, c in enumerate(chunks)]


def pack(src, transcript_path, out, title, created_at, tx_id="words",
         recorded_at_local=None):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,31}", tx_id) or tx_id in RESERVED_IDS:
        raise ValueError(f"invalid transcript id {tx_id!r}")
    prefix = "CASSINI_TX_" + tx_id.upper().replace("-", "_") + "_PAYLOAD_"

    head, audio, audio_pages, serial = parse(open(src, "rb").read())
    channels = head[9]
    if channels not in (1, 2):
        raise ValueError(f"the ogg-opus profile accepts 1 or 2 channels, not {channels}")
    opus_sha, samples = audio_digest(head, audio, audio_pages[-1]["granule"])
    duration_ms = samples * 1000 // 48000

    doc = json.load(open(transcript_path))
    speakers = doc["speakers"]
    items = doc.get("items") or [
        {"speaker": seg["speaker"], "startMs": w["startMs"],
         "endMs": w["endMs"], "text": w["text"]}
        for seg in doc.get("segments", []) for w in seg["words"]]
    body = {"format": "cassini.words.v1", "wordCount": len(items), "items": items}
    b_raw, b_gz, b_chunks, b_sha = encode_payload(body)

    shape = {"sampleRate": 48000, "channels": channels,
             "sampleCount": samples, "durationMs": duration_ms}
    manifest = {
        "kind": "cassini-portable-meeting", "version": 1, "profile": "ogg-opus",
        "meeting": {"id": "mtg_" + opus_sha, "title": title,
                    "createdAtUtc": created_at, "durationMs": duration_ms},
        "audio": dict(container="ogg", codec="opus", **shape),
        "integrity": dict(matchPolicy="exact-opus-audio-v1",
                          opusAudioSha256=opus_sha, **shape),
        "speakers": speakers,
        "transcripts": [{
            "id": tx_id, "default": True,
            "format": "cassini.words.v1", "wordCount": len(items),
            "payloadRef": {"prefix": prefix, "chunkCount": len(b_chunks),
                           "sha256": b_sha, "rawBytes": len(b_raw),
                           "gzipBytes": len(b_gz),
                           "mime": "application/vnd.cassini.transcript-words+json",
                           "encoding": "base64url+gzip+utf8json"}}]}
    if recorded_at_local:
        manifest["meeting"]["recordedAtLocal"] = recorded_at_local
    m_raw, m_gz, m_chunks, m_sha = encode_payload(manifest)

    comments = [
        ("TITLE", title), ("DATE", created_at), ("DESCRIPTION", DESCRIPTION),
        ("ENCODER", VENDOR),
        ("CASSINI_FORMAT", "org.cassini.portable-meeting/1"),
        ("CASSINI_PROFILE", "ogg-opus"),
        ("CASSINI_DECODE_HINT", DECODE_HINT),
        ("CASSINI_MEETING_ID", "mtg_" + opus_sha),
        ("CASSINI_CREATED_AT", created_at),
        ("CASSINI_SPEAKER_COUNT", str(len(speakers))),
        ("CASSINI_AUDIO_SAMPLE_RATE", "48000"),
        ("CASSINI_AUDIO_CHANNELS", str(channels)),
        ("CASSINI_AUDIO_SAMPLE_COUNT", str(samples)),
        ("CASSINI_AUDIO_DURATION_MS", str(duration_ms)),
        ("CASSINI_AUDIO_MATCH_POLICY", "exact-opus-audio-v1"),
        ("CASSINI_AUDIO_OPUS_SHA256", opus_sha),
        ("CASSINI_TRANSCRIPT_IDS", tx_id),
        ("CASSINI_TRANSCRIPT_DEFAULT", tx_id),
        ("CASSINI_PAYLOAD_SCHEMA",
         "https://format.gocassini.com/schema/cassini-portable-meeting-manifest-v1.schema.json"),
    ]
    if recorded_at_local:
        comments.append(("CASSINI_RECORDED_AT_LOCAL", recorded_at_local))
    comments += chunk_tags("CASSINI_PAYLOAD_",
                           "application/vnd.cassini.portable-meeting+json",
                           m_raw, m_gz, m_chunks, m_sha)
    comments += chunk_tags(prefix, "application/vnd.cassini.transcript-words+json",
                           b_raw, b_gz, b_chunks, b_sha)
    comments.sort()             # ASCII order, as the reference producer writes it

    # Repaginate: BOS page with OpusHead, then OpusTags across as many pages as
    # it needs, then every original audio page verbatim with a fresh sequence
    # number and CRC. Granule stays 0 for both header packets.
    tags_pkt = build_tags_packet(VENDOR, comments)
    pages = [make_page(serial, 0, 0x02, 0, lace(len(head)), head)]
    lacing, off, seq = lace(len(tags_pkt)), 0, 1
    while lacing:
        take, lacing = lacing[:255], lacing[255:]
        n = sum(take)
        pages.append(make_page(serial, seq, 0x01 if off else 0x00, 0,
                               take, tags_pkt[off:off + n]))
        off += n
        seq += 1
    for page in audio_pages:
        header = bytearray(page["header"])
        struct.pack_into("<I", header, 18, seq)
        struct.pack_into("<I", header, 22, 0)
        raw_page = bytearray(header) + page["lacing"] + page["payload"]
        struct.pack_into("<I", raw_page, 22, ogg_crc(bytes(raw_page)))
        pages.append(bytes(raw_page))
        seq += 1
    open(out, "wb").write(b"".join(pages))

    # The claim this file exists to make: tagging did not touch the audio.
    head2, audio2, pages2, _ = parse(open(out, "rb").read())
    check, _ = audio_digest(head2, audio2, pages2[-1]["granule"])
    if check != opus_sha:
        raise ValueError(f"self-check failed: {check} != {opus_sha}")
    print(f"wrote {out}  opus_sha256={opus_sha}  words={len(items)}  "
          f"comments={len(comments)}  manifest_chunks={len(m_chunks)}  "
          f"transcript_chunks={len(b_chunks)}  audio digest unchanged")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("audio"), ap.add_argument("transcript"), ap.add_argument("out")
    ap.add_argument("--title", required=True)
    ap.add_argument("--created-at", required=True, metavar="RFC3339")
    ap.add_argument("--recorded-at-local", metavar="ISO8601")
    ap.add_argument("--transcript-id", default="words")
    a = ap.parse_args()
    try:
        pack(a.audio, a.transcript, a.out, a.title, a.created_at,
             a.transcript_id, a.recorded_at_local)
    except ValueError as exc:
        sys.exit(f"cassini-pack: {exc}")
