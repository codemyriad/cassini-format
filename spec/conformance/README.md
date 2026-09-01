# Conformance vectors

Twenty-two `.opus` files and one index, for answering "does my reader conform"
with something other than a person's judgement.

```bash
python3 run-conformance.py --adapter 'node adapters/adapter-js.mjs'
```

```console
16 pass, 4 warn, 0 fail, 2 skip, of 22
```

An adapter is any command that takes one file path and prints one observation
JSON object on stdout. Nothing else about your reader is assumed, so a reader in
any language needs about forty lines to join in. The four in `adapters/` are the
worked examples.

`index.json` names every vector, what it contains, which specification section it
exercises, and what a conforming reader must observe. It is the contract; this
directory is CC0 so you can vendor the whole thing.

## Profiles

A reader that never touches the audio cannot verify the audio digest, and should
not be marked down for it.

* `metadata` — reads the tags and the payload. Vectors 010 and 011 are skipped.
* `full` — also verifies `CASSINI_AUDIO_OPUS_SHA256` against the Opus packets.

## What the vectors cover

The happy path, and then every edge the specification either decides or has
quietly left open: plain audio with no metadata, multi-chunk payloads, padded
base64url, duplicate and missing chunks, chunk counts that disagree with what is
present, wrong payload and audio digests, lower- and mixed-case tag names,
unknown manifest members, an unknown major version, two transcripts, a transcript
id with no chunk set, and a comment header larger than the 61,440 octets
[RFC 7845 §5.2](https://www.rfc-editor.org/rfc/rfc7845#section-5.2) lets a reader
ignore.

Vectors 018 and 021 are the pair worth reading first. They carry the same 48
comments with the same values in the same 65,351-octet packet, and differ only in
write order:

```
018-oversize-opustags     65,351 octets   24 comments past the limit, 17 load-bearing
021-descriptors-first     65,351 octets    3 comments past the limit,  0 load-bearing
```

That is the whole argument for writing descriptor tags before chunk tags, in two
files.

## Where the readers stand today

```
tools/cassini-extract.py            13 pass,  7 warn, 0 fail, 2 skip
tools/cassini-extract.py + digest   15 pass,  7 warn, 0 fail, 0 skip
tools/cassini-read.js               16 pass,  4 warn, 0 fail, 2 skip
cassini inspect (gocassini)          8 pass,  6 warn, 8 fail, 0 skip
```

Those eight failures are fixed by
[gocassini#230](https://github.com/codemyriad/gocassini/pull/230), which takes
the reference reader to 12 pass, 10 warn, 0 fail. Until it merges, the numbers
above are what `origin/main` scores.

A warning is a vector where the specification has decided nothing yet, so the
reader cannot be wrong. A failure is a reader disagreeing with a rule that exists.

The reference implementation's eight failures come from four causes, all listed
in [`../../ERRATA.md`](../../ERRATA.md):

* it refuses padded base64url, which the specification's own worked example
  produces (vector 004)
* it takes a transcript's chunk count from the tag rather than from
  `payloadRef.chunkCount`, so it fails on files this repository's other readers
  decode (007, 008)
* it reports `ok` on files whose transcript it cannot reach, because the word
  count it prints is the one the manifest claims rather than one it counted
  (005, 006, 020, 022)
* it adds the word counts of alternative transcripts together, so a three-word
  meeting carrying two transcripts of it reports six (016)

## The trust state

`expect.state` is the normative name from
[`SPEC.md`](../../SPEC.md)'s "Trust and integrity": one of `plain-audio`,
`unknown-cassini-format`, `invalid-cassini-metadata`, `unverified`,
`stale-audio`, `ok`. It is the thing two readers must agree on when they
describe one file.

The `classification` / `payloadTrust` / `audioTrust` triple is kept alongside it
because it carries more detail, and an adapter that reports only the triple still
validates.

How much work a reader did changes which state is correct, and the harness knows
this. A reader on the `metadata` profile never looks at the audio, so it cannot
reach `ok` or `stale-audio` and must say `unverified`. Where a vector only
requires `unverified`, a reader that did check the audio and found it sound may
report `ok`: it did strictly more than was asked. `stale-audio` is never
accepted in place of `unverified`, because that is a real disagreement rather
than extra diligence.

## Adding a vector

Keep it small: the largest here is 65 KB and most are under 4 KB. Add the file,
add its entry to `index.json` with the observation a conforming reader must make,
and say in `rationale` what would go wrong if nobody checked it.
