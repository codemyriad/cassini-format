We built [gocassini](https://github.com/codemyriad/gocassini) to record and
transcribe Nextcloud Talk calls, and found that a single audio file carrying
its own timed transcript was more useful than a recording plus a sidecar. This
site publishes that format so anyone can use it. Version 1 was published on
2026-09-02.

## Who uses it

gocassini, internally. Every meeting it records is written this way. That is
the only producer and, apart from the readers in this repository, the only
consumer. The format is published so that other things can be built on it: a
transcript viewer for meetings, a podcast with its transcript embedded, or
[a song with its synchronized lyrics in the audio file](/demo/).

If you build something that reads or writes these files, or try to and hit a
wall, please [open an issue](https://github.com/codemyriad/cassini-format/issues).

## Stable

The container and transport in `org.cassini.portable-meeting/1` remain stable.
`CASSINI_FORMAT`, the payload chunk naming, `base64url+gzip+utf8json`, the
`CASSINI_TX_<ID>_PAYLOAD_` prefix scheme and the `cassini.words.v1` body shape
are used by shipped software.

## Simplification and implementation status

The 2026-09-07 revision removes the required origin labels from word-timed
transcripts, the withdrawn LLM cleanup slot, and metadata the production
writer never fills. Multiple transcripts, display documents, summaries and
processing provenance remain.

The [Cassini follow-up](https://github.com/codemyriad/gocassini/pull/276)
updates the Go packer and inspector, browser viewer and static exporter to
accept both simplified entries and old origin labels. The readers and demos
on this site use the simplified contract. Earlier Cassini builds that require
`role` need the follow-up before opening newly produced files; merging the
implementation does not itself update an installed app.

See the [audit and implementation details](https://github.com/codemyriad/cassini-format/blob/main/design/format-simplification-2026-09-07.md)
for the comparison against current main and what remains supported.

The
[conformance suite](https://github.com/codemyriad/cassini-format/tree/main/spec/conformance)
checks both older files and transcripts without origin labels. Run it against
your reader; its results distinguish required behavior from advisory warnings.
