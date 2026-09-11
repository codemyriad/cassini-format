We needed a format for [gocassini](https://github.com/codemyriad/gocassini), our
small app for recording and transcribing Nextcloud Talk calls. We wanted to
find a passage in the transcript and listen to what was actually said.
Keeping the audio and timed words in one file lets us check the transcription,
including after sharing it. That worked well for our meetings, so we published
what we were using. Version 1 was published on 2026-09-02.

We vibe coded it, and we dogfood it. The readers, examples and conformance checks
help us test the result, but our experience is still mostly with our own app
and recordings. We think it is useful and would like to find out where it helps
other people, or where it falls short.

## Who uses it

We do, in gocassini. Every meeting it records is written this way. Alongside
that app, this repository has standalone readers, a producer and the browser
demo. We do not yet have independent adoption to report.

Other uses, such as interviews, podcasts or [synchronized lyrics](/demo/),
are possibilities to explore. [Using Cassini](/using/) explains the workflow,
available tools and limits so you can judge whether a small trial makes sense.

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
was merged to main as [`4c7f8bd`](https://github.com/codemyriad/gocassini/commit/4c7f8bda30e9fc4f652f98ed31554734cb5c1b87).
The Go packer and inspector, browser viewer and static exporter now
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
