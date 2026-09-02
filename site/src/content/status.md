The format ships. Every meeting gocassini records is written this way and the
files are in people's hands. Nothing here is a plan.

## Stable

The wire strings in `org.cassini.portable-meeting/1` are not going to move.
`CASSINI_FORMAT`, the payload chunk naming, `base64url+gzip+utf8json`, the
`CASSINI_TX_<ID>_PAYLOAD_` prefix scheme, the manifest's top-level members and
the `cassini.words.v1` body shape are load-bearing in shipped software.

Read them as frozen, even without a ceremony declaring it.

## Where the document and the software disagree

The spec has been revised to say what a real file contains, so the remaining gap
runs the other way: rules the document states that the reference readers do not
follow yet. Padded base64url is refused by one of them, none of them bounds the
decompression, and the six trust-state names are not the names they print. All
of it is in [the errata](/errata/), with the evidence.

That list is the biggest thing standing between this and a format someone else
can pick up.

## Undecided

**Whether the format keeps the product's name.** Settled: it does. One argument
said a format meant to outlive one program should not be named after it. The
counter, which won, is that SQLite's file format is named after the one product
that writes it and became an archival format anyway.
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
