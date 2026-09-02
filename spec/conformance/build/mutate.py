"""Build the negative and edge-case vectors from the two positive ones.

Every vector here is a comment-list edit: the audio pages are copied verbatim,
so apart from 010 (which deliberately pairs one file's tags with another
file's audio) every vector in the suite carries the same audio essence as the
positive vector it was derived from.

SPDX-License-Identifier: CC0-1.0
"""
import base64, copy, gzip, hashlib, json, sys
import opustags
from opustags import pack

OUT = "../opus/"


def load(src):
    return opustags.read_comments(src)


def write(src, name, comments, vendor="cassini-pack.py"):
    opustags.write_comments(src, OUT + name, comments, vendor=vendor)
    import pathlib
    print(f"{name:38} {len(comments):3d} comments  "
          f"{pathlib.Path(OUT + name).stat().st_size:6d} B")


def edit(comments, name, value):
    """Replace the value of one comment, keeping its position."""
    return [(n, value if n == name else v) for n, v in comments]


def drop(comments, name):
    return [(n, v) for n, v in comments if n != name]


def decode_set(comments, prefix):
    tags = dict(comments)
    n = int(tags[prefix + "CHUNK_COUNT"])
    b64 = "".join(tags[f"{prefix}{i:03d}"] for i in range(n))
    return json.loads(gzip.decompress(
        base64.urlsafe_b64decode(b64 + "=" * (-len(b64) % 4))))


def replace_set(comments, prefix, obj, mime):
    """Re-encode a chunk set in place, updating all six descriptors."""
    raw, gz, chunks, sha = pack.encode_payload(obj)
    # CASSINI_PAYLOAD_SCHEMA lives inside the manifest chunk set's own prefix
    # but is not one of its six descriptors, so it must survive a re-encode.
    kept = [(n, v) for n, v in comments
            if not n.startswith(prefix) or n == "CASSINI_PAYLOAD_SCHEMA"]
    return sorted(kept + pack.chunk_tags(prefix, mime, raw, gz, chunks, sha))


MANIFEST_MIME = "application/vnd.cassini.portable-meeting+json"
WORDS_MIME = "application/vnd.cassini.transcript-words+json"

one = load(OUT + "001-minimal-v1.opus")[1]
three = load(OUT + "003-multichunk-v1.opus")[1]

# --- 004  padded base64url in every chunk of both sets ----------------------
def repad(comments):
    out = []
    for n, v in comments:
        if n.endswith(tuple(f"_{i:03d}" for i in range(1000))) and "PAYLOAD" in n:
            out.append((n, v))
        else:
            out.append((n, v))
    return out

def pad_last_chunk(comments, prefix):
    """base64url padding is only meaningful on the LAST chunk of a set: the
    concatenation is what gets decoded."""
    tags = dict(comments)
    n = int(tags[prefix + "CHUNK_COUNT"])
    last = f"{prefix}{n - 1:03d}"
    joined = "".join(tags[f"{prefix}{i:03d}"] for i in range(n))
    padding = "=" * (-len(joined) % 4)
    return [(k, v + padding if k == last else v) for k, v in comments]

c = pad_last_chunk(one, "CASSINI_PAYLOAD_")
c = pad_last_chunk(c, "CASSINI_TX_RAW_ASR_PAYLOAD_")
write(OUT + "001-minimal-v1.opus", "004-padded-base64url-v1.opus", c)

# --- 005  a chunk tag that appears twice ------------------------------------
c = list(three)
i = next(k for k, (n, _) in enumerate(c) if n == "CASSINI_TX_RAW_ASR_PAYLOAD_001")
c.insert(i + 1, c[i])                       # byte-identical repeat
write(OUT + "003-multichunk-v1.opus", "005-duplicate-chunk-tag.opus", c)

# --- 006  a chunk missing from the middle of a set --------------------------
c = drop(three, "CASSINI_TX_RAW_ASR_PAYLOAD_001")
write(OUT + "003-multichunk-v1.opus", "006-missing-chunk.opus", c)

# --- 007  CHUNK_COUNT higher than the chunks present ------------------------
c = edit(three, "CASSINI_TX_RAW_ASR_PAYLOAD_CHUNK_COUNT", "4")
write(OUT + "003-multichunk-v1.opus", "007-chunk-count-too-high.opus", c)

# --- 008  CHUNK_COUNT lower than the chunks present -------------------------
c = edit(three, "CASSINI_TX_RAW_ASR_PAYLOAD_CHUNK_COUNT", "2")
write(OUT + "003-multichunk-v1.opus", "008-chunk-count-too-low.opus", c)

# --- 009  a payload digest that does not match the payload ------------------
c = edit(one, "CASSINI_PAYLOAD_SHA256", "0" * 64)
write(OUT + "001-minimal-v1.opus", "009-bad-payload-sha256.opus", c)

# --- 010  correct, self-consistent metadata over the WRONG audio ------------
#          (vector 003's whole comment list, pasted onto vector 001's audio)
write("base-tiny.opus", "010-stale-audio.opus", three)

# --- 011  the tag and the manifest disagree about the audio digest ----------
c = edit(one, "CASSINI_AUDIO_OPUS_SHA256", "f" * 64)
write(OUT + "001-minimal-v1.opus", "011-tag-manifest-disagreement.opus", c)

# --- 012 / 013  tag-name case ------------------------------------------------
write(OUT + "001-minimal-v1.opus", "012-lowercase-tag-names.opus",
      [(n.lower(), v) for n, v in one])
write(OUT + "001-minimal-v1.opus", "013-mixed-case-tag-names.opus",
      [("".join(ch.lower() if i % 2 else ch for i, ch in enumerate(n)), v)
       for n, v in one])

# --- 014  an unknown member in the manifest, which must be ignored ----------
m = decode_set(one, "CASSINI_PAYLOAD_")
m["cassiniFutureField"] = {"note": "a member from a later revision", "n": 7}
m["speakers"][0]["pronouns"] = "she/her"
write(OUT + "001-minimal-v1.opus", "014-unknown-manifest-member.opus",
      replace_set(one, "CASSINI_PAYLOAD_", m, MANIFEST_MIME))

# --- 015  an unknown MAJOR version ------------------------------------------
m = decode_set(one, "CASSINI_PAYLOAD_")
m["version"] = 99
c = replace_set(one, "CASSINI_PAYLOAD_", m, MANIFEST_MIME)
c = edit(c, "CASSINI_FORMAT", "org.cassini.portable-meeting/99")
write(OUT + "001-minimal-v1.opus", "015-unknown-major-version.opus", c)

# --- 016  two transcripts, exactly one flagged default ----------------------
body = decode_set(one, "CASSINI_TX_RAW_ASR_PAYLOAD_")
alt = copy.deepcopy(body)
for it in alt["items"]:
    it["text"] = it["text"].upper()
ALT = "CASSINI_TX_SECOND_PASS_PAYLOAD_"
c = replace_set(one, ALT, alt, WORDS_MIME)      # add the second body
m = decode_set(one, "CASSINI_PAYLOAD_")
entry = copy.deepcopy(m["transcripts"][0])
entry.update(id="second-pass", role="raw-asr", default=False)
raw, gz, chunks, sha = pack.encode_payload(alt)
entry["payloadRef"].update(prefix=ALT, chunkCount=len(chunks), sha256=sha,
                           rawBytes=len(raw), gzipBytes=len(gz))
m["transcripts"].append(entry)
c = replace_set(c, "CASSINI_PAYLOAD_", m, MANIFEST_MIME)
c = edit(c, "CASSINI_TRANSCRIPT_IDS", "raw-asr,second-pass")
write(OUT + "001-minimal-v1.opus", "016-two-transcripts.opus", sorted(c))

# --- 017  an id in CASSINI_TRANSCRIPT_IDS with no chunk set behind it -------
c = edit(one, "CASSINI_TRANSCRIPT_IDS", "raw-asr,ghost")
write(OUT + "001-minimal-v1.opus", "017-dangling-transcript-id.opus", c)

# --- 018 / 021  a comment header past the 61,440-octet window --------------
# RFC 7845 5.2 lets a reader ignore comments not wholly inside the first 61,440
# octets. These two carry the SAME comments with the SAME values in the SAME
# size of packet, and differ only in the order they are written, which is the
# whole argument for putting descriptors first.
#
# The bulk has to be incompressible, or gzip folds it away and the header never
# reaches the window. A SHA-256 chain is deterministic on every platform.
def incompressible(n, seed=b"cassini-conformance-018"):
    out, h = bytearray(), seed
    while len(out) < n:
        h = hashlib.sha256(h).digest()
        out += h
    return bytes(out[:n])

m = decode_set(one, "CASSINI_PAYLOAD_")
m["attachments"] = [{"id": "bulk", "mime": "application/octet-stream",
                     "contentBase64": base64.b64encode(incompressible(48_000)).decode()}]
big = replace_set(one, "CASSINI_PAYLOAD_", m, MANIFEST_MIME)

def chunky(name):
    return name.startswith("CASSINI_PAYLOAD_") and name[-3:].isdigit()

def descriptor(name):
    """A load-bearing comment that is not a numbered chunk: CASSINI_FORMAT and
    the six descriptors of each chunk set. Chunk tags past the window are
    unavoidable once the header is bigger than the window; descriptors past it
    are a producer's choice."""
    return name == "CASSINI_FORMAT" or (
        name.startswith(("CASSINI_PAYLOAD_", "CASSINI_TX_")) and not name[-3:].isdigit())

WINDOW = 61_440

def past_window(comments, vendor="cassini-pack.py"):
    """Comments not wholly inside the first WINDOW octets of the OpusTags
    packet, laid out per RFC 7845 5.2: magic, vendor, count, then each comment
    as a 4-byte length and its bytes."""
    at = 8 + 4 + len(vendor.encode()) + 4
    total, descriptors = 0, 0
    for n, v in comments:
        at += 4 + len(f"{n}={v}".encode())
        if at > WINDOW:
            total += 1
            descriptors += descriptor(n)
    return at, total, descriptors

ascii_order = sorted(big)
desc_first = sorted(big, key=lambda kv: (chunky(kv[0]), kv[0]))
size, past18, bear18 = past_window(ascii_order)
size21, past21, bear21 = past_window(desc_first)
assert size == size21 > WINDOW, f"OpusTags packet is {size} octets, not past {WINDOW}"
assert int(dict(big)["CASSINI_PAYLOAD_CHUNK_COUNT"]) > 1, "manifest must span several chunks"
assert sorted(ascii_order) == sorted(desc_first) and ascii_order != desc_first
assert bear18 > 0 and bear21 == 0, (bear18, bear21)
print(f"018/021: {size} octets, {len(big)} comments; past the window: "
      f"{past18} ({bear18} descriptors) in 018, {past21} ({bear21} descriptors) in 021")

write(OUT + "001-minimal-v1.opus", "018-oversize-opustags.opus", ascii_order)
write(OUT + "001-minimal-v1.opus", "021-descriptors-first.opus", desc_first)
assert open(OUT + "018-oversize-opustags.opus", "rb").read() != \
       open(OUT + "021-descriptors-first.opus", "rb").read()

# --- 019  the manifest chunk count claims one more chunk than exists -------
c = edit(one, "CASSINI_PAYLOAD_CHUNK_COUNT", "2")
write(OUT + "001-minimal-v1.opus", "019-manifest-chunk-count-too-high.opus", c)

# --- 020 / 022  the same chunk tag twice, in both orders -------------------
# A first-wins reader passes one of these and fails the other; a last-wins
# reader does the opposite. Only a reader that refuses both is right.
# 003's multi-chunk set is the transcript body, not the manifest.
DUP = "CASSINI_TX_RAW_ASR_PAYLOAD_001"
JUNK = "Xn9" * 40
at = next(k for k, (n, _) in enumerate(three) if n == DUP)
real = three[at][1]
head, tail = three[:at], three[at + 1:]         # the repeat stays in place
write(OUT + "003-multichunk-v1.opus", "020-duplicate-chunk-differing.opus",
      head + [(DUP, JUNK), (DUP, real)] + tail)
write(OUT + "003-multichunk-v1.opus", "022-duplicate-chunk-junk-last.opus",
      head + [(DUP, real), (DUP, JUNK)] + tail)
