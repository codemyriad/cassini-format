# The transcript body: `cassini.words.v1`

Date: 2026-09-01

Status: first written definition. Describes what shipped files contain.

A transcript body is the document the timestamps actually live in. It is what
`CASSINI_TX_<UPPER_ID>_PAYLOAD_000..N` decodes to in a v2 or v3 file, and what
`manifest.transcript` holds inline in a v1 file. Those two are the same document
type, which is why v2 could call itself "purely a transport change" and mean it.

Until now the string `cassini.words.v1` existed in the repository only as a
value. This is the definition. Nothing here is new: it is what the reference
producer has been writing all along, transcribed from the code and checked
against real files.

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

That is the whole format. Four members on the envelope, four required fields per
item, two optional ones.

## Requirements

A conforming transcript body:

1. **MUST** be a single JSON object, encoded as UTF-8.

2. **MUST** carry `format`, a string. For this version it is the literal
   `cassini.words.v1`. Producers MUST write it. Consumers SHOULD NOT dispatch on
   it, because the manifest entry's `format` field already told them what they
   are about to decode, and no shipped reader has ever compared the two.

3. **MUST** carry `items`, an array. Each element is an item as defined below.
   An empty transcript is `[]`. Consumers **SHOULD** also accept `null` here and
   treat it as empty, because Go's encoder emits `null` for a nil slice and a
   producer written in Go can reach that path.

4. **MUST** carry `wordCount`, an integer equal to `items.length`. It is a
   convenience for a reader that wants the number before parsing the array. On
   disagreement, `items` wins.

5. **MAY** carry `language`, a BCP-47 tag or a bare language code. Consumers
   **MUST** treat an absent `language` and an empty `language` as the same
   thing: nobody said. Both occur in shipped files, because the Go producer
   omits the member and a JavaScript repacker in the reference tree writes `""`.
   Neither means "not English". The reference producer does not currently
   populate it on any path.

6. **MUST NOT** be assumed closed. A consumer that meets a member it does not
   recognise ignores it and carries on.

An item:

7. **MUST** carry `speaker`, a string matching an `id` in the manifest's
   `speakers[]`. That entry's `label` is the name a reader displays; it is a
   human-facing string with no format of its own, and it can be absent, in which
   case show the `id`. If `speaker` matches no entry at all, the item is still
   transcript content: render it with an unknown speaker rather than dropping
   it.

8. **MUST** carry `startMs` and `endMs`, integers, milliseconds from the start of
   the audio program. `endMs` **SHOULD** be greater than or equal to `startMs`.

9. Items are in **speaker-turn order**, not global time order, and a consumer
   **MUST NOT** sort them by `startMs`.

   Within one speaker's run `startMs` increases. Across a speaker change it can
   go backwards, because people talk over each other and each speaker's words are
   kept together. Sorting by time interleaves the words of overlapping speakers
   and destroys every turn in the file.

   Read them in file order. In the demo file, 7 of 669 items start earlier than
   the item before them, and every one of those is at a speaker change.

10. A **turn** is a maximal run of consecutive items with the same `speaker`.
    That is the unit a reader should render as a paragraph, and reconstructing
    turns needs nothing but a single pass in file order. A turn starts at its
    first item's `startMs` and ends at the greatest `endMs` among its items,
    which is not always the last item's. A producer **SHOULD** keep one
    speaker's continuous speech in one run rather than splitting it.

11. **MUST** carry `text`, a string. It is the token as spoken, punctuation
   attached, with no leading or trailing space. Joining `items[].text` with a
   single space reconstructs readable prose, which is exactly what the reference
   readers do.

12. **MAY** carry `attributionGapDb`, a number. At this word, how far the
    loudest *other* participant's microphone sat above its own noise floor
    compared with the attributed speaker's, in dB. Near zero means the
    attributed speaker was the loudest voice. A large positive value means
    somebody else was, and this word is a crosstalk candidate.

    The key is present exactly on the words the attribution stage measured. A
    measured `0` **is written**, so presence is the signal and absence means
    "not measured". A consumer **MUST NOT** read a missing key as zero.

13. **MAY** carry `lowConfidenceSpeaker`, a boolean, and only ever as `true`. A
    confidently attributed word omits the key rather than writing `false`. The
    word is still canonical transcript content: a consumer MAY de-emphasise it,
    exclude it from a summary, or surface it for review, but MUST NOT silently
    drop it.

14. A file whose attribution stage never ran carries neither key on any item,
    and is byte-identical to a file packed before those fields existed.

## Conventions

None of this is required, and all of it is what the reference implementation
does.

* **One item is one word.** The producer emits one item per word, and every
  shipped file is like that. The format does not forbid an item covering a
  longer span, and one reader already tolerates it, but nothing produces it and
  a consumer is not expected to handle prosody or sub-word splits.

* **Blank text is skipped, not emitted.** The producer drops words with empty
  text rather than writing an item with `"text": ""`.

* **Overlapping speech is normal.** Two speakers' items can cover the same
  milliseconds. Nothing in the format says a moment belongs to one speaker.

* **Milliseconds, not seconds, and not frames.** The manifest's `durationMs` is
  the same clock. Both derive from the Opus 48 kHz sample clock.

* **The MIME type written into the tags is
  `application/vnd.cassini.transcript-words+json`.** It is a hint. Nothing
  dispatches on it either.

* **A derived transcript uses this same body shape.** A readable cleanup or a
  display version is still `items[]` of words; what makes it derived is its
  `role` and its `sourceTranscriptId` in the manifest, not a different body.

  In the reference implementation this path is currently unreachable: the pack
  input has no way to set `sourceTranscriptId`, and the validator rejects a
  derived entry without one. So no shipped file carries a second body today. The
  shape above is what one will contain when it does.

## What is deliberately not here

There is no per-item `id`, no confidence score, no alternatives list, no
word-level language tag, and no link back to a source segment. All of those
exist upstream in the pipeline's own working files and are dropped on the way
into the portable file, because the portable file is the thing that has to
survive being mailed to somebody.

If a future version wants them, it takes a new format id and the manifest entry
says so. Adding a member to this one is allowed; changing what an existing
member means is not.

## Schema

[`cassini-words-v1.schema.json`](cassini-words-v1.schema.json), CC0.

It is deliberately open: unknown members validate, on the envelope and on the
item. A typo in an optional hint should cost you the hint, not the transcript.
