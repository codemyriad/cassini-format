# The name is not decided

Date of the discussion: 2026-08-28. Still open on 2026-09-01.

Freeze item 5 wants the brand out of the wire, which means picking a string that
gets frozen into every file: tag prefix, format id, media type, schema URL, spec
title. It is the one decision on the freeze list that genuinely cannot be
revised later.

The real question is narrower than "pick a name". It is **product name, or its
own name**, and the name falls out of that.

## CASSINI

Zero wire migration, zero alias table, the files already say it. SQLite's file
format is named after the one product that writes it and became a Library of
Congress-recommended archival format anyway.

The env-var collision (item 5: `CASSINI_` doubles as a config prefix in ~170
places) even inverts here: instead of renaming nine wire strings you rename ~170
*deployment* env vars, which is local config rather than bytes on disk.

Cost: a spec named after one vendor's product reads as that vendor's private
format. That matters only if third-party producers are actually wanted. "The
format should have its own identity, Cassini just one user of it" was the
opening framing of the whole exercise, so this is really a question of whether
that goal has softened.

## Cairn

The pick *given* the independent-identity premise: a marker left in a durable
medium so whoever comes next can read it, which is the format's function.
Pronounceable, and nothing in format space uses it. Used throughout the public
page draft as the working name.

Weakness: it tells you nothing about what the file contains.

## CAWT

Argued against, and not because it's an acronym (PDF, PNG and FLAC are acronyms
and did fine). It sits between the two stools: you pay the full rename cost, but
the C still stands for Cassini, so you don't buy the neutrality the rename was
for. If the brand tie stays, plain CASSINI is strictly better — one name instead
of two.

One rescue if the word itself appeals: it is a homophone of "caught", which is
apt for a recording format, and acronyms can be re-expanded. "Container for
Audio With Transcript" keeps CAWT and drops the product from the expansion. Then
it is a real contender.

## What this repository does meanwhile

Everything here still uses the shipped `CASSINI_` / `org.cassini.portable-meeting/N`
wire strings, because those are what real files contain. The public page draft
([`public-page-draft-2026-08-28.md`](public-page-draft-2026-08-28.md)) is written
in `CAIRN_` because it was drafted as the future public site. Nothing has been
renamed in a file yet.
