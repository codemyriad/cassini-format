#!/usr/bin/env python3
"""Package the reviewed NASA/JPL demo. No AI calls; requires ffmpeg.

Usage: python3 site/scripts/produce-cassini-final.py /path/to/source.m4v
The source URL and SHA-256 are in the checked-in production record.
SPDX-License-Identifier: CC0-1.0
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
DEMO = ROOT / 'site/static/demo'
STEM = 'cassini-final-moments'
record = json.loads((DEMO / f'{STEM}.production.json').read_text())
source = Path(sys.argv[1])
if hashlib.sha256(source.read_bytes()).hexdigest() != record['source']['sha256']:
    raise SystemExit('Source digest differs from the reviewed video')
spec = importlib.util.spec_from_file_location('cassini_pack', ROOT / 'tools/cassini-pack.py')
pack = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pack)
encode = pack.encode_payload
build_tags = pack.build_tags_packet


def encode_with_provenance(obj):
    if obj.get('kind') == 'cassini-portable-meeting':
        obj['provenance'] = {'demoProduction': record}
    return encode(obj)


def tags_with_credit(vendor, comments):
    return build_tags(vendor, sorted(comments + [
        ('ARTIST', 'NASA/JPL-Caltech'),
        ('COPYRIGHT', 'Courtesy NASA/JPL-Caltech. Source material subject to JPL image use policy.'),
        ('SOURCE', record['source']['page']),
        ('LICENSE', 'https://www.jpl.nasa.gov/jpl-image-use-policy/'),
        ('COMMENT', 'Reconciled transcript by codemyriad; not an official NASA transcript. See embedded provenance. No NASA/JPL-Caltech endorsement implied.'),
    ]))


pack.encode_payload = encode_with_provenance
pack.build_tags_packet = tags_with_credit
with tempfile.TemporaryDirectory(prefix='cassini-final-') as work:
    audio = str(Path(work) / 'audio.opus')
    # Audio-only decode: VAAPI is a video accelerator and is not needed here.
    subprocess.run(['ffmpeg', '-v', 'error', '-i', str(source), '-map', '0:a:0',
                    '-vn', '-map_metadata', '-1', '-c:a', 'libopus', '-b:a', '96k',
                    '-ar', '48000', audio], check=True)
    pack.pack(audio, DEMO / f'{STEM}.words.json', DEMO / f'{STEM}.opus',
              'Final Moments in Cassini Mission Control', record['createdAtUtc'])
