"""OpusTags surgery for building conformance vectors.

Loads tools/cassini-pack.py as a library (it is the only stdlib producer we
have) and adds the two things a vector builder needs that a producer must never
do: write an arbitrary comment list, and rewrite the comment list of a file
that is already packed.

SPDX-License-Identifier: CC0-1.0
"""
import importlib.util, pathlib, struct, sys

TOOLS = pathlib.Path(__file__).resolve().parents[3] / "tools"
_spec = importlib.util.spec_from_file_location("cassini_pack", TOOLS / "cassini-pack.py")
pack = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pack)


def read_comments(path):
    """Return (vendor, [(name, value), ...]) from a file's OpusTags packet."""
    data = pathlib.Path(path).read_bytes()
    packets, partial, out = [], b"", []
    for page in pack.read_pages(data):
        cur = 0
        for n in page["lacing"]:
            partial += page["payload"][cur:cur + n]
            cur += n
            if n == 255:
                continue
            packets.append(partial)
            partial = b""
        if len(packets) >= 2:
            break
    tags = packets[1]
    assert tags[:8] == b"OpusTags", "second packet is not OpusTags"
    at = 8
    vlen = struct.unpack_from("<I", tags, at)[0]; at += 4
    vendor = tags[at:at + vlen].decode(); at += vlen
    count = struct.unpack_from("<I", tags, at)[0]; at += 4
    for _ in range(count):
        n = struct.unpack_from("<I", tags, at)[0]; at += 4
        field = tags[at:at + n].decode("utf-8"); at += n
        name, _, value = field.partition("=")
        out.append((name, value))
    return vendor, out


def write_comments(src, dst, comments, vendor=None):
    """Copy src to dst with its OpusTags comment list replaced verbatim.

    Every audio page is copied byte for byte apart from its sequence number and
    CRC, so the exact-opus-audio-v1 digest is unchanged by construction.
    """
    data = pathlib.Path(src).read_bytes()
    head, audio, audio_pages, serial = pack.parse(data)
    if vendor is None:
        vendor, _ = read_comments(src)
    tags_pkt = pack.build_tags_packet(vendor, comments)
    pages = [pack.make_page(serial, 0, 0x02, 0, pack.lace(len(head)), head)]
    lacing, off, seq = pack.lace(len(tags_pkt)), 0, 1
    while lacing:
        take, lacing = lacing[:255], lacing[255:]
        n = sum(take)
        pages.append(pack.make_page(serial, seq, 0x01 if off else 0x00, 0,
                                    take, tags_pkt[off:off + n]))
        off += n
        seq += 1
    for page in audio_pages:
        header = bytearray(page["header"])
        struct.pack_into("<I", header, 18, seq)
        struct.pack_into("<I", header, 22, 0)
        raw = bytearray(header) + page["lacing"] + page["payload"]
        struct.pack_into("<I", raw, 22, pack.ogg_crc(bytes(raw)))
        pages.append(bytes(raw))
        seq += 1
    pathlib.Path(dst).write_bytes(b"".join(pages))
