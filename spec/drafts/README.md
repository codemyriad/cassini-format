# Pre-publication drafts

Date: 2026-09-01

Two wire formats came before the published one. Both were used only inside
Cassini, neither was ever documented publicly, and no file carrying them left the
project. They are kept here because files in those formats still exist on our own
disks and something has to be able to read them.

Nothing in this directory is part of the published specification. Do not
implement from it. If you are writing a reader, you will never meet one of these
files.

They are also a naming hazard: draft 1 identified itself as
`org.cassini.portable-meeting/1`, which is the identifier the published format
now uses for a different and incompatible shape. Draft 1 is distinguishable by
`integrity.matchPolicy = exact-pcm` and by carrying a singular `transcript`
object where the published format has a `transcripts` array.

* `manifest-draft-1.schema.json`, `manifest-draft-2.schema.json` — their manifest schemas
* `example-draft-2-two-transcripts.json` — a draft-2 manifest
* `drafts.md` — what each one changed


## A quirk of draft 1 worth recording

`sampleCount` in a draft-1 manifest was computed before encoding, so it is 312
samples and 7 ms larger than the audio the file actually plays. The PCM digest
matches; only the shape disagrees. A reader that treats that as a mismatch
reports a failure on nine files that are entirely intact, so check the digest
and let the shape difference pass.

## Retagging a draft file

A tool that rewrites the tags on a draft file MUST NOT relabel its
`CASSINI_AUDIO_MATCH_POLICY`, and MUST NOT reinterpret a PCM digest as a
compressed-audio one. Converting a draft to the published format means
recomputing the digest from the Opus packets, which changes the meeting id; it
is a repack, not a retag.
