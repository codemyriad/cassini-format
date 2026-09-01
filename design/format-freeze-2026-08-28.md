# The format freeze

Date: 2026-08-28
Status: proposal, mostly outstanding
Source: <https://silvio-cassini-format-freeze.pgs.sh/> (drafted with Claude Code
over two multi-agent review passes of the gocassini repo, each finding put
through an adversarial verification pass; the measured claims were re-run in a
checkout)

Publishing the format freezes it. Tag names, the manifest schema and the media
types become someone else's compatibility problem the moment a third party
implements them. These are the changes wanted in before that happens.

The "landed?" notes were added on 2026-09-01 by checking the gocassini tree, not
by rerunning the measurements.

## 1. Hash the audio packets, not decoded PCM (must)

**Landed** in `org.cassini.portable-meeting/3` on 2026-08-29 as
`exact-opus-audio-v1`. See [`../spec/cassini-opus-audio-integrity-v1.md`](../spec/cassini-opus-audio-integrity-v1.md).

The reason it had to change: Opus decoders don't guarantee bit-exact output, and
the two decoders inside one ffmpeg binary disagree about the same shipped file.

```console
$ ffmpeg -c:a opus    -i meeting.opus -f s16le … | sha256sum
995cf949d127f3b3c270c6f5…   matches the manifest
$ ffmpeg -c:a libopus -i meeting.opus -f s16le … | sha256sum
8f1f52bf40dac2d9262d133f…   the reference decoder disagrees
```

Meeting identity depended on which decoder you linked. A digest over the Opus
audio packets is deterministic and survives exactly what reprocessing does:

| operation | digest | |
|---|---|---|
| original | `213e1a45…` | 52,313 audio packets |
| `ffmpeg -c copy` | `213e1a45…` | |
| tag rewrite | `213e1a45…` | reprocessing does this |
| remux `.opus` → `.ogg` | `213e1a45…` | |
| re-encode 48k | `36b3ebf3…` | real change, still caught |

Packet hash 0.02s against decode + PCM hash 1.22s. The cost is that every
`meeting.id` changes once.

## 2. The digest is a join key, not a seal (must)

**Outstanding.** `matchPolicy` is still in the v3 schema; the integrity rules in
[`../SPEC.md`](../SPEC.md) still say discard. `containerSha256` is gone from v3.

The spec's integrity rules were written to catch edited audio. That is not the
lifecycle. In practice the audio never changes and the transcript does
(reprocessing with a newer Cassini is the normal life of a file). Rule 3 makes
discarding the transcript a MUST when any integrity field disagrees, and it
fired on every shipped file, because `sampleCount` was computed before encoding
and was short by exactly the 312-sample Opus pre-skip:

```console
$ cassini inspect meeting.opus
… pcm_sha256=995cf949…  matches
warning=sample count mismatch: manifest=50220480 actual=50220168
fallback=plain-audio
```

* Replace rule 3: on a mismatch the reader **keeps** the transcript and labels
  it unverified.
* Move the hard check to the producer, where it already exists (pack re-reads
  its own output and refuses to ship a mismatch).
* Delete `matchPolicy` (a one-value const whose name promises a bit-exactness
  Opus refuses to guarantee).
* Delete `containerSha256` (declared in both schemas, written by nothing, and
  guaranteed to break on every legitimate reprocess if anyone implemented it).

This also turns repacking the old files from urgent into optional.

## 3. Let it grow without a version bump (must)

**Outstanding.** `additionalProperties: false` still appears 13 times in the v3
schema.

Both schemas say `additionalProperties: false` at the root and in ten nested
places, `version` is a const integer, and nothing says what a reader does with a
member it doesn't recognise. Net effect: any field nobody has thought of yet is
a new major version, and both shipped readers throw on it.

* Consumers MUST ignore unknown tags and unknown manifest members.
* Promote the per-transcript chunk-set mechanism (`payloadRef`: hashed,
  self-describing, the best idea in the format) to a top-level `payloads[]` with
  an open `kind`, so summaries, source maps and captions have a home.
* Reserve a vendor namespace, in the tags and in the manifest.
* Keep `payloadRef` and `integrity` closed: a typo there is a decode failure,
  not a lost hint.

## 4. Say which Cassini wrote the file (must)

**Outstanding.**

`provenance.*.version` exists in the schema and in the Go struct and is assigned
by nothing; the bundle writer carries only `backend`, `model` and `device`. So
the one fact you need to decide whether a file is worth reprocessing (which
Cassini made it) is the one fact no file records. Add a producer tag
(`implementation`/`version`) and populate the provenance version. Additive, no
schema change.

## 5. Take the brand out of the wire (must)

**Outstanding, and blocked on the name (see [naming.md](naming.md)).**

Nine strings are baked into every file and all of them say Cassini: the
`CASSINI_` tag prefix, `org.cassini.portable-meeting/2`, the manifest `kind`,
three `vnd.cassini` media types, the `cassini.local` schema URL (a placeholder
that does not resolve), the `payloadRef.prefix` regex, and the body format id
`cassini.words.v1`.

That last one is doubly broken: branded, and defined nowhere. The string appears
in the repo only as a value, and the Go producer and the JS viewer disagree
about the shape it names. **The body schema has to be written before any of this
ships.**

One rule whatever the name wins: the tag prefix must never double as an env-var
or config prefix. `CASSINI_` does today, in about 170 places, and that is
exactly what makes this rename risky.

## 6. Publish as version 2 (must)

**Contradicted by what shipped.** gocassini went to `org.cassini.portable-meeting/3`
on 2026-08-29, a day after this was written.

Files already in users' hands say `org.cassini.portable-meeting/1` and `/2`. If
the renamed format starts at `/1`, two different wire formats will permanently
call themselves 1. The proposal was to publish today's format as `<name>/2` and
list the legacy identifiers in a compatibility section. With `/3` now shipped
this needs redeciding: the renamed format presumably starts at `/3` or `/4`, and
the alias table grows a row.

## 7. Licence the spec so people can implement it (must)

**Applied in this repository on 2026-09-01**, pending confirmation.

The spec text and both schemas were AGPL-3.0, which makes a standard nobody can
safely implement. CC-BY-4.0 for the prose, CC0 for schemas and test vectors,
AGPL stays on the Cassini implementation. Plus a patent non-assertion and one
line separating the format name from the product name.

## 8. Write the non-goals down (should)

**Outstanding in the spec** (the public page draft states them).

* No supersession model: a reprocessed file replaces its predecessor. Modelling
  the lineage was considered and rejected as too much machinery for the benefit.
* No promise to survive audio edits made by format-unaware tools.
* Digests prove the transcript and the audio belong together, not that either is
  authentic.
* No new file extension, no new media type: the file is `audio/ogg` and stays
  that.

None of this is a limitation to hide. Stating it saves every implementer a wrong
guess.

## 9. Small fixes (should)

**Outstanding.**

* Drop `_` from transcript ids: `raw-asr` and `raw_asr` currently map to the
  same tag prefix.
* Match field names case-insensitively (the Vorbis spec says so; both readers
  assume otherwise).
* Define chunk reassembly by tag index, define behaviour on duplicate or missing
  chunks, and pick a base64url padding rule. The producer writes unpadded, the
  Go reader rejects padded, and the spec's own example re-pads.
* Bound decompression while inflating, not after.
* Stop writing internal service endpoints (`processingStep.baseUrl`, `host`)
  into cleartext tags.
* Make "the format tag is the first comment" normative, so a libmagic signature
  is possible.

## 10. Not the format, but before anything else (bug)

**Appears addressed since.** `retag.go` now carries unknown tags forward and has
a `retag_test.go` covering it, but nobody has re-run the destructive case.

`npm run reprocess:portable` destroyed v2 files. The tag rewrite runs ffmpeg
with `-map_metadata -1` (strip everything), and the tag builder pinned
`version: 1` and never emitted `CASSINI_TX_*` tags, so every v2 transcript body
was dropped and the result was renamed over the original.

## Checklist

- [x] packet digest replaces exact-pcm; check published URLs that embed `meeting.id`
- [ ] integrity rules rewritten: join key, reader keeps the transcript
- [ ] ignore-unknowns rules, `payloads[]`, vendor namespace
- [ ] producer version recorded in the file
- [ ] all nine wire strings renamed; `words/1` body schema written
- [x] licence split
- [ ] non-goals section in the spec
- [x] guard or fix the retag path
