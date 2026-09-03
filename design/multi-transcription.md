# Why each transcript has its own chunk set

Date: 2026-05-12

This is the design discussion behind the per-transcript chunk sets in the
specification. It was written when the format carried exactly one transcript
per file, and the option it recommends is the one that shipped. Version numbers
in the original proposal predate the published `org.cassini.portable-meeting/1`
and are omitted here.

## Motivation

Swapping the speech-to-text model requires publishing the new transcript next
to the old one for side-by-side inspection. With one transcript per file the
only ways to do that were two `.opus` files or a sidecar JSON, and neither
matches the promise of one file that plays anywhere.

The same shape covers four other cases: keeping the previous engine's transcript
when the model changes, several cleanup runs against the same raw ASR, a
human-corrected transcript alongside the raw one, and a translated transcript
next to the original.

## Parse cost: what splitting actually saves

If N transcripts share one JSON blob, every load decompresses and parses all of
them, because `JSON.parse` is a whole-document operation. For current sizes that
is affordable: a one-hour word-timed transcript is about 720 KB of JSON (about
80 bytes per item over 9,000 words), 220 KB gzipped, and V8 parses it in 5 to
8 ms. Two transcripts cost about 15 ms, five about 40 ms.

So parse cost alone does not force a split. What splitting buys is structural:
each body has its own SHA-256 and is independently verifiable, a corrupt or
oversized body does not taint the others, bodies of different `format` versions
can coexist, and a transcript can be added or removed without rewriting the
manifest hash. Skipping the decompression of bodies you do not display comes
along for free. Tag extraction from the Ogg comment header is byte slicing and
stays cheap regardless.

## Design options

**A: one blob with an array inside.** Add `transcripts: []` to the manifest
payload. Simplest schema change and no new tag namespaces, but every load pays
for every transcript, individual transcripts cannot be hash-verified, one bad
body taints the manifest, and the single tag grows.

**B: a separate chunk set per transcript.** The manifest stays small and carries
an index; each body has its own `CASSINI_TX_<ID>_PAYLOAD_*` chunk set with its
own descriptors and SHA-256. Independent integrity per body, lazy decompression,
room for different body formats. The cost is more tag namespaces and one more
step for the reader: resolve the descriptor, fetch the chunks, decompress,
parse.

**C: each transcript as a base64 `attachments` entry.** No schema churn, but
attachments are opaque to the spec: no provenance, no default selection, no
`format` discriminator. The file no longer says "this is a transcript you can
switch to".

**D: sidecar files.** Rejected from the start; it breaks the one-file promise.

## Recommendation

Option B, with two guardrails that are now normative in the specification:

1. At most one default transcript per slot, so a reader that wants "the"
   transcript can resolve it without a choice.
2. A fixed tag naming rule: transcript ids match `^[a-z0-9][a-z0-9_-]{0,31}$`,
   and the tag prefix is the id upper-cased with `-` turned into `_`. Each chunk
   set carries the same descriptors as the manifest's.
