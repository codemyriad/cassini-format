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

The wire strings in `org.cassini.portable-meeting/1` are not going to move.
`CASSINI_FORMAT`, the payload chunk naming, `base64url+gzip+utf8json`, the
`CASSINI_TX_<ID>_PAYLOAD_` prefix scheme, the manifest's top-level members and
the `cassini.words.v1` body shape are load-bearing in shipped software. A change
to any of them is a new major version.

## What the software still owes the specification

The document is ahead of the code in a few places: padded base64url is refused
by one reader, none of them yet bounds the decompression against the declared
`RAW_BYTES`, and the six trust-state names are not the names they print. The
[conformance suite](https://github.com/codemyriad/cassini-format/tree/main/spec/conformance)
is where each of those shows up as a warning, and it is the thing to run against
your own reader. The gocassini change that writes `version: 1` and the
`scripted` role is an open pull request.
