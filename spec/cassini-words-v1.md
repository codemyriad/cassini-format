# The transcript body: `cassini.words.v1`

Date: 2026-09-02

Status: published

A transcript body is the document the timestamps live in. It is what a
`CASSINI_TX_<UPPER_ID>_PAYLOAD_` chunk set decodes to: one JSON object, one item
per word, each item naming who said it and when.

## The shape

```json
{
  "format": "cassini.words.v1",
  "language": "en",
  "wordCount": 3,
  "items": [
    { "speaker": "spk_mira", "startMs": 900,  "endMs": 1251, "text": "Morning." },
    { "speaker": "spk_mira", "startMs": 1251, "endMs": 1502, "text": "Sorry," },
    { "speaker": "spk_leo",  "startMs": 5012, "endMs": 5238, "text": "And",
      "attributionGapDb": 17.25, "lowConfidenceSpeaker": true }
  ]
}
```

That is the whole format.

## The envelope

| Member | | Rule |
|---|---|---|
| `format` | MUST | the literal `cassini.words.v1`. Consumers SHOULD NOT dispatch on it; the manifest entry already said what this is. |
| `items` | MUST | an array of items. Empty is `[]`. Consumers SHOULD accept `null` as empty, because a Go encoder emits it for an empty slice. |
| `wordCount` | MUST | equal to `items.length`. A convenience; `items` wins on disagreement. |
| `language` | MAY | BCP-47 or a bare code. Absent and empty mean the same thing: nobody said. Neither means English. |

The envelope MUST be a single UTF-8 JSON object, and a consumer MUST ignore any
member it does not recognise.

## An item

| Member | | Rule |
|---|---|---|
| `speaker` | MUST | an `id` from the manifest's `speakers[]`. That entry's `label` is what a reader displays. |
| `startMs`, `endMs` | MUST | integers, milliseconds from the start of the audio, `0 ≤ startMs ≤ endMs`. The interval is half-open: the word ends before `endMs`. An end past the audio's duration is allowed; the word ran into silence. |
| `text` | MUST | one token, punctuation attached, no surrounding space. In a language written with spaces, joining items with one space reconstructs prose; the format carries no separator. |
| `attributionGapDb` | MAY | see below |
| `lowConfidenceSpeaker` | MAY | see below |

An item whose `speaker` matches no entry is still transcript content. Render it
under an unknown speaker; do not drop it.

## Order

Items are in **speaker-turn order**, not time order. Within one speaker's run,
`startMs` never decreases; two words can share a start. Across a speaker change it can go backwards, because people
talk over each other and each speaker's words are kept together.

A consumer MUST NOT sort items by `startMs`. Sorting by time interleaves
overlapping speakers and destroys every turn in the file. Read them in file
order.

A **turn** is a maximal run of consecutive items with the same `speaker`. It is
the unit a reader renders as a paragraph, and one pass in file order
reconstructs every turn. A turn starts at its first item's `startMs` and ends at
the greatest `endMs` among its items, which is not always the last item's.
Producers SHOULD keep one speaker's continuous speech in one run.

## Attribution

Two optional members record how sure the attribution stage was about `speaker`.

`attributionGapDb`: at this word, how far the loudest *other* participant's
microphone sat above its own noise floor, compared with the attributed
speaker's, in dB. Near zero means the attributed speaker was the loudest voice.
Large and positive means somebody else was, and this word is a crosstalk
candidate. How the producer measured it is its own business, and
`provenance.attribution.mode` names the method; the number is evidence, not a
defined quantity. The key is present exactly on the words that were measured. A
measured `0` is written, so presence is the signal, and a consumer MUST NOT read
absence as zero.

`lowConfidenceSpeaker`: only ever `true`. A confidently attributed word omits
the key. The word is still canonical content: a consumer MAY de-emphasise it or
flag it for review, but MUST NOT drop it.

A file whose attribution stage never ran carries neither key on any item.

## Conventions

Not required; what the reference producer does.

- One item is one word. The format does not forbid a longer span, but nothing
  produces one.
- Blank text is skipped, not written.
- Two speakers' items can cover the same milliseconds. Nothing says a moment
  belongs to one speaker.
- Milliseconds throughout, on the same clock as the manifest's `durationMs`.
- The media type written into the tags is
  `application/vnd.cassini.transcript-words+json`. It is a hint.
- The same word-timed body can carry recognised or authored text. No origin
  label is required. Display transcripts have their own body format, named by
  their manifest entry; they are not `cassini.words.v1` documents.

## What is deliberately not here

No per-item `id`, no confidence score, no alternatives, no word-level language,
no link to a source segment. Those exist in the pipeline's working files and
are dropped on the way in, because this file is the one that has to survive
being mailed to somebody.

Adding a member is allowed. Changing what an existing member means is a new
format id.

## Schema

[`cassini-words-v1.schema.json`](cassini-words-v1.schema.json), CC0. It is
open: unknown members validate on both the envelope and the item. A typo in an
optional hint should cost you the hint, not the transcript.
