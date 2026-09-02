Version 1 of the format was published on 2026-09-02. Every meeting gocassini
records is written this way and the files are in people's hands. Nothing here is
a plan.

## Stable

The wire strings in `org.cassini.portable-meeting/1` are not going to move.
`CASSINI_FORMAT`, the payload chunk naming, `base64url+gzip+utf8json`, the
`CASSINI_TX_<ID>_PAYLOAD_` prefix scheme, the manifest's top-level members and
the `cassini.words.v1` body shape are load-bearing in shipped software. A change
to any of them is a new major version.

## What the software still owes the specification

Rules the document states that the reference readers do not follow yet: padded
base64url is refused by one of them, none of them bounds the decompression, and
the six trust-state names are not the names they print. All of it is in
[the errata](/errata/), with the evidence. The gocassini change that writes
`version: 1` and the `scripted` role is an open pull request.

## Open

**A second implementation.** There isn't one. One implementation is not an
ecosystem, and most of why this site exists is to find out whether that can
change. The name question was settled: the format keeps the product's name, for
the reason SQLite's file format keeps its.
[The argument in full](/design/naming/).

**What a second implementation would need.** I do not know, because there isn't
one. The honest answer to "who else implements this" is nobody, and one
implementation is not an ecosystem. Most of why this repository exists is to find
out whether that can change.

If you have built something that reads or writes these files, or tried to and hit
a wall, I would like to hear about it. The walls are more useful.

## The full arguments

The [design notes](/design/) carry them, dates and all. The
[freeze list](/design/format-freeze-2026-08-28/) is the complete inventory.
