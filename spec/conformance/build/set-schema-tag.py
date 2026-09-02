#!/usr/bin/env python3
"""Set CASSINI_PAYLOAD_SCHEMA on packed files.

The tag is REQUIRED and names the schema the manifest conforms to. Only the
comment list changes: write_comments copies every audio page byte for byte, so
exact-opus-audio-v1 and the meeting id derived from it cannot move.

    python3 set-schema-tag.py <url> <file>...

SPDX-License-Identifier: CC0-1.0
"""
import sys, pathlib, opustags

CANON = "CASSINI_PAYLOAD_SCHEMA"


def spell(comments):
    """Match the file's own casing.

    Vorbis field names are case-insensitive, and two vectors deliberately write
    them lower-cased and alternating. Adding a canonical upper-case name to
    those would create a duplicate field, which is a different defect from the
    one they are testing.
    """
    fmt = next((n for n, _ in comments if n.upper() == "CASSINI_FORMAT"), None)
    if fmt is None or fmt.isupper():
        return CANON
    if fmt.islower():
        return CANON.lower()
    # Alternating: follow the same parity the file already uses.
    upper_first = fmt[0].isupper()
    return "".join(c.upper() if (i % 2 == 0) == upper_first else c.lower()
                   for i, c in enumerate(CANON))


def apply(path, url):
    vendor, comments = opustags.read_comments(path)
    if not any(n.upper() == "CASSINI_FORMAT" for n, _ in comments):
        return "plain audio, skipped"
    name_to_use = spell(comments)
    out, seen = [], False
    for name, value in comments:
        if name.upper() == CANON:
            out.append((name, url)); seen = True
        else:
            out.append((name, value))
    if not seen:
        # Keep ASCII order, which is where a reader expects to find it.
        out.append((name_to_use, url))
        out.sort(key=lambda kv: kv[0])
    tmp = str(path) + ".tmp"
    opustags.write_comments(path, tmp, out, vendor=vendor)
    pathlib.Path(tmp).replace(path)
    return "set" if not seen else "updated"

url = sys.argv[1]
for p in sys.argv[2:]:
    print(f"  {pathlib.Path(p).name:38} {apply(p, url)}")
