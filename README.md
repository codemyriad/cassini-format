# cassini-format

A Cassini portable meeting is an ordinary `.opus` file. Any player plays it,
because that is all it is: Ogg Opus, 48 kHz. It also carries its own
word-timestamped transcript, the speakers, and a record of what produced the
text, in the OpusTags header, where a player that does not care ignores them.

The website is <https://cassini-format.codemyriad.io/>. Everything on it is
built from this repository.

## What is here

* [`SPEC.md`](SPEC.md): the specification. Version 1, published 2026-09-02.
* [`spec/`](spec/): the two JSON Schemas; the transcript body
  ([`cassini-words-v1.md`](spec/cassini-words-v1.md)); the audio digest
  ([`cassini-opus-audio-integrity-v1.md`](spec/cassini-opus-audio-integrity-v1.md));
  the [conformance suite](spec/conformance/); and the
  [private drafts](spec/drafts/) that came before version 1.
* [`tools/`](tools/): small readers and a producer in Python and JavaScript,
  standard library only, meant to be copied.
* [`site/`](site/): the website, and under `site/static/demo/` a real file to
  check against.
* [`design/`](design/): the notes the decisions were made from. Historical.
* [`LICENSE.md`](LICENSE.md): CC-BY-4.0 prose, CC0 everything an implementer
  copies.

## Try it on a file

```bash
tools/cassini-extract.py meeting.opus --tags   # the descriptor tags
tools/cassini-extract.py meeting.opus --list   # which transcripts are inside
tools/cassini-extract.py meeting.opus          # the manifest as JSON
tools/cassini-read-pure.py meeting.opus        # no ffprobe: parses the container itself
```

## The shape of it

Two layers of metadata. The first is plain comments any tool shows: `TITLE`,
`CASSINI_SPEAKER_COUNT`, `CASSINI_AUDIO_OPUS_SHA256`. The second is a JSON
manifest, gzipped, base64url-encoded and split across numbered comments. Each
transcript body is a second such payload under its own prefix.

```text
CASSINI_FORMAT=org.cassini.portable-meeting/1
CASSINI_PAYLOAD_ENCODING=base64url+gzip+utf8json
CASSINI_PAYLOAD_CHUNK_COUNT=1
CASSINI_PAYLOAD_SHA256=a4d048386f81bd4b...
CASSINI_PAYLOAD_000=H4sIAAAAAAAC_61W227jNhD9...
CASSINI_TX_SCRIPT_PAYLOAD_CHUNK_COUNT=3
CASSINI_TX_SCRIPT_PAYLOAD_000=H4sIAAAAAAAC_...
CASSINI_DECODE_HINT=Concatenate CASSINI_PAYLOAD_000..N for the manifest; ...
```

`CASSINI_DECODE_HINT` is there so that someone with `ffprobe` and no
documentation still gets the transcript out. A message in a bottle.

Three commitments run through it:

* **Progressive enhancement.** A player that understands nothing plays the
  audio. A reader that understands the tags gets everything.
* **Keep what a better model could use later.** The words a recogniser
  produced survive next to any cleanup, with provenance saying what made each.
* **The digest is a join key, not a seal.** A SHA-256 over the Opus packets
  says whether this transcript describes this recording. It catches accidents,
  not adversaries.

## Implementations

The reference producer is [gocassini](https://github.com/codemyriad/gocassini),
which records, transcribes and packs these files. The readers in `tools/` and
on the site are the others. If you build one, say so: a format that only one
program reads is not really a format.

Issues and pull requests welcome.
