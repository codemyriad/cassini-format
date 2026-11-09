"""Build the meeting-time vectors, 027-029.

Each carries a misleading recordedAtLocal: the digits of a server clock running
in UTC for a meeting held in Rome, an hour behind the site's wall clock. A
reader that prefers the label, or that falls back to createdAtUtc, shows the
wrong time; the expected reading in index.json is the one SPEC.md "When the
meeting happened" gives.

Run from any directory. Audio packets are copied verbatim from 001.
SPDX-License-Identifier: CC0-1.0
"""
from pathlib import Path
import subprocess
import sys

from opustags import read_comments, write_comments

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "opus"
ROOT = HERE.parents[2]

CREATED = "2026-11-09T10:47:02Z"        # packed after transcription
STARTED = "2026-11-09T09:31:48.250Z"    # playback position 0
LABEL = "2026-11-09T09:31:48"           # UTC digits posing as Rome wall clock


def pack(name, title, *extra):
    subprocess.run([
        sys.executable, str(ROOT / "tools/cassini-pack.py"),
        str(OUT / "001-minimal-v1.opus"), str(HERE / "tiny-transcript.json"),
        str(OUT / name), "--title", title, "--created-at", CREATED,
        "--recorded-at-local", LABEL, *extra,
    ], check=True)


def main():
    # recordedAtUtc, its mirror tag and DATE all carry the start.
    pack("027-recorded-at-utc.opus", "Recording start in UTC",
         "--recorded-at-utc", STARTED)

    # What an ExApp file packed before 2026-11-09 looks like: DATE is the pack
    # stamp, so it says nothing about the meeting, and only the label is left.
    pack("028-date-is-created-at.opus", "DATE is the pack stamp")

    # A producer that knows the site's zone writes DATE with an offset and no
    # recordedAtUtc. DATE names the start; the label is still not converted.
    pack("029-date-with-offset.opus", "DATE with an offset")
    path = OUT / "029-date-with-offset.opus"
    vendor, comments = read_comments(path)
    comments = [(k, "2026-11-09T10:31:48+01:00" if k == "DATE" else v) for k, v in comments]
    write_comments(path, path, comments, vendor)


if __name__ == "__main__":
    main()
