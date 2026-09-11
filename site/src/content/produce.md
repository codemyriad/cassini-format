Use this guide to turn existing audio and timed words into a file someone else
can open. First package the example, then substitute your own inputs and check
the result before sharing it.

You need **Python 3 and curl** for the first example. The producer uses only
the Python standard library. Recording, speech recognition and any audio
conversion happen before this step; [Using Cassini](/using/#what-do-you-have-today)
explains the path from different starting materials.

## Write your first file

In a fresh directory, download the [CC0 producer](https://github.com/codemyriad/cassini-format/blob/main/tools/cassini-pack.py),
the example audio and its matching word data:

```bash
curl -fLO https://raw.githubusercontent.com/codemyriad/cassini-format/main/tools/cassini-pack.py
curl -fLO https://format.gocassini.com/demo/{{demo.filename}}
curl -fLO https://format.gocassini.com/demo/{{demo.wordInput}}
python3 cassini-pack.py {{demo.filename}} {{demo.wordInput}} meeting.opus \
  --title "My portable recording" --created-at 2026-09-09T09:00:00Z
```

The result is `meeting.opus`, containing **{{demo.words}} words** and
**{{demo.speakers}} speakers**. The command prints `audio digest unchanged`
after reading back the output and comparing the compressed audio with the input.
[Open the result](/try/) to read and listen to your newly packaged file.

The sample source already has Cassini metadata. This exercise uses its audio
and supplies the words again. The packer writes a new manifest from the supplied
inputs; it does not merge existing transcripts or other metadata from the source.

## Use your own inputs

Replace the audio and JSON paths, title and date in the command. Your source
must be Ogg Opus. Your JSON supplies the speaker table and the words that
actually describe that recording:

```json
{
  "speakers": [{ "id": "sam", "label": "Sam" }],
  "items": [
    { "speaker": "sam", "startMs": 900, "endMs": 1300, "text": "Hello." }
  ]
}
```

Times are integer milliseconds from the start of the audio. Each word's
`speaker` identifies an entry in `speakers`. Keep words in speaker-turn order,
including overlaps; sorting the whole list by time changes how conversations
are reconstructed. See the [word format](/spec/words-v1/) for exact rules.

The packer also accepts `segments` instead of `items`:

```json
{
  "speakers": [{ "id": "sam", "label": "Sam" }],
  "segments": [
    { "speaker": "sam", "words": [
      { "startMs": 900, "endMs": 1300, "text": "Hello." }
    ] }
  ]
}
```

Use these exact field names and millisecond units when adapting speech-recognition
output. This is a supported JSON input shape, not a general importer for every
transcription service. Speaker attribution and transcription accuracy remain
the responsibility of the pipeline that supplied them.

## Check and share the result

The producer's self-check establishes that packaging preserved the audio digest.
Before sharing, [check the embedded data, audio claim and JSON structure](/verify/)
and open the result in the recipient's software. That guide supplies all of its
tool downloads and names its additional prerequisites.

An ordinary Ogg Opus player can play your output. A Cassini reader can also show
the embedded transcript. [What the recipient needs](/using/#what-the-recipient-needs)
explains that distinction and the current applications.

The sections below describe the encoding and requirements for implementing a
producer yourself. The [specification](/spec/) is the normative reference.

## What you are making

An Ogg Opus file at 48 kHz, mono for speech, with two things in its OpusTags
comment header: plain comments a human can read, and a JSON manifest gzipped,
base64url-encoded and cut into numbered pieces.

## Requirements

1. Container **MUST** be Ogg, codec **MUST** be Opus, sample rate field
   `48000`. Mono for speech; stereo only when it is deliberate.

2. **MUST** carry `CASSINI_FORMAT=org.cassini.portable-meeting/1`. That is what
   makes it a Cassini file.

3. **MUST** carry every descriptor tag, each with a non-empty value:

   | tag | value |
   |---|---|
   | `CASSINI_FORMAT` | `org.cassini.portable-meeting/1` |
   | `CASSINI_PROFILE` | `ogg-opus` |
   | `CASSINI_PAYLOAD_MIME` | `application/vnd.cassini.portable-meeting+json` |
   | `CASSINI_PAYLOAD_ENCODING` | `base64url+gzip+utf8json` |
   | `CASSINI_PAYLOAD_SCHEMA` | `https://format.gocassini.com/schema/cassini-portable-meeting-manifest-v1.schema.json` |
   | `CASSINI_PAYLOAD_CHUNK_COUNT` | decimal integer, 1 or more |
   | `CASSINI_PAYLOAD_SHA256` | lowercase hex, over the **decompressed** JSON |
   | `CASSINI_PAYLOAD_RAW_BYTES` | decimal integer, the decompressed length |
   | `CASSINI_PAYLOAD_GZIP_BYTES` | decimal integer, the compressed length |
   | `CASSINI_TRANSCRIPT_IDS` | the ids in `transcripts[]`, comma-separated, no spaces, sorted |
   | `CASSINI_TRANSCRIPT_DEFAULT` | the id a viewer opens first |
   | `CASSINI_TX_<UPPER_ID>_PAYLOAD_MIME` | per transcript: `application/vnd.cassini.transcript-words+json` |
   | `CASSINI_TX_<UPPER_ID>_PAYLOAD_ENCODING` | per transcript: `base64url+gzip+utf8json` |
   | `CASSINI_TX_<UPPER_ID>_PAYLOAD_CHUNK_COUNT` | per transcript: decimal integer |
   | `CASSINI_TX_<UPPER_ID>_PAYLOAD_SHA256` | per transcript: lowercase hex, over the decompressed body |
   | `CASSINI_TX_<UPPER_ID>_PAYLOAD_RAW_BYTES` | per transcript: decimal integer |
   | `CASSINI_TX_<UPPER_ID>_PAYLOAD_GZIP_BYTES` | per transcript: decimal integer |
   | `CASSINI_AUDIO_SAMPLE_RATE` | `48000` |
   | `CASSINI_AUDIO_CHANNELS` | `1` or `2` |
   | `CASSINI_AUDIO_SAMPLE_COUNT` | playable samples, as the digest spec defines them |
   | `CASSINI_AUDIO_DURATION_MS` | `sampleCount * 1000 / 48000`, truncating |
   | `CASSINI_AUDIO_MATCH_POLICY` | `exact-opus-audio-v1` |
   | `CASSINI_AUDIO_OPUS_SHA256` | lowercase hex, the audio digest |
   | `CASSINI_DECODE_HINT` | one sentence explaining the chunk sets |

   The six `CASSINI_TX_*` descriptors are copies of the entry's `payloadRef`.
   The full list, with the exact `DECODE_HINT` sentence, is in
   [the specification](/spec/v1/#cassini-descriptor-tags).

4. Build the payload in this order: compact UTF-8 JSON, gzip, base64url
   **without padding**, split.

5. Chunks **MUST** be `CASSINI_PAYLOAD_NNN`, zero-padded to a *minimum* of
   three digits, from `000`, joined by index with no separator, exactly
   `CHUNK_COUNT` of them. Index 1000 is `CASSINI_PAYLOAD_1000`, not truncated
   and not four-padded from the start. Keep each value at or under 4096
   characters. Not an Ogg requirement; it keeps the header readable in ordinary
   tools.

6. Each chunk-set SHA-256 is over the **decompressed** JSON bytes, not the gzip
   stream and not the base64 text. `CASSINI_AUDIO_OPUS_SHA256` is different: it
   is over the packet stream that [`exact-opus-audio-v1`](/spec/audio-integrity/)
   defines.

7. The manifest **MUST** have `kind`, `version`, `profile`, `meeting`, `audio`,
   `integrity`, `speakers`, `transcripts`. `kind` is the literal
   `cassini-portable-meeting` and `profile` the literal `ogg-opus`, in every
   version of the format.

8. Each transcript body lives in its own chunk set, under a prefix derived from
   the id by upper-casing and replacing `-` with `_`: `raw-asr` becomes
   `CASSINI_TX_RAW_ASR_PAYLOAD_`. The entry's `payloadRef` carries that prefix,
   the chunk count and the body's SHA-256.

   So ids **MUST NOT** contain `_`: `raw-asr` and `raw_asr` map to the same
   prefix and one silently wins. In practice `^[a-z0-9][a-z0-9-]{0,31}$`.

9. Ids **MUST NOT** be a reserved descriptor name: `payload`, `format`, `audio`,
   `meeting`, `integrity`, `transcript`, `provenance`, `summary`,
   `attachments`, `speakers`.

10. **At most one** entry flagged `default: true` per slot — one across
    `transcripts[]`, one across the `display` entries in `readableTranscripts[]`.
    Flagging none is legal and readers fall back to array order.
    `CASSINI_TRANSCRIPT_DEFAULT` mirrors the words slot. Word-timed entries
    carry no `role`. A display entry carries `role: "display"` and
    `sourceTranscriptId` naming its word-timed source.

11. `CASSINI_AUDIO_OPUS_SHA256` is computed over the canonical compressed Opus
    stream, **without decoding the audio**. The rule is in
    [the digest spec](/spec/audio-integrity/): playback-relevant `OpusHead`
    fields, every audio packet in order with its length, the playable sample
    count. It excludes `OpusTags` and all Ogg framing, which is what lets the
    manifest contain its own audio digest without writing it changing it.

12. Descriptor tags **MAY** be written before the chunk tags.

    [RFC 7845 §5.2](https://www.rfc-editor.org/rfc/rfc7845#section-5.2) lets a
    reader ignore comments past the first 61,440 octets, and the payload is
    easily larger than that, so on a long recording the descriptors can fall
    outside the window. Nothing truncates in practice: `ffmpeg -c copy`, a remux
    to `.ogg` and a mutagen round-trip all preserve every comment on a 307 KB
    header. The descriptor block is about 1,388 bytes, so writing it first costs
    nothing.

13. Verify your own output before shipping it: read it back, recompute both
    digests, refuse to publish a mismatch. The producer is the right place for
    the strict check, because it can fix the problem and a reader cannot.

14. Keep the original word transcript beside derived display text, so its
    words and timings remain available for comparison and reprocessing.

## Conventions

Not required. All of it is what the reference producer does.

* **Write `TITLE`, `DATE` and a `DESCRIPTION`** saying in one line how to decode
  the payload. They cost nothing and they are what somebody sees on right-click.

* **Do not bother with `ENCODER`.** The producer sets `Cassini`, ffmpeg's Ogg
  muxer overwrites it with `encoder=Lavf…`, so nothing in a Cassini file records
  which program wrote it.

* **Write a summary tag only when you have a value.** Absent, never empty.

* **Never put a room token, join link or internal service URL in a tag.** These
  files get mailed to people. The reference producer derives a one-way
  `rm_<16 hex>` for `roomId` so that publishing a recording does not also hand
  out the credential that joins the live conversation.

* **The manifest is the record; summary tags are the copy.** Edit one, edit the
  other. A consumer finding them disagreeing believes the manifest.

## A complete producer

`tools/cassini-pack.py` builds a valid file with nothing but the Python
standard library. No ffmpeg, no Go. It walks the Ogg pages, computes the digest,
builds the manifest, and rewrites only the `OpusTags` packet, copying every audio
page across untouched and patching the page sequence numbers and CRCs.

The digest excludes `OpusTags` and all Ogg framing, so tagging cannot change
it: compute it once.

`tools/cassini-opus-digest.py` computes `exact-opus-audio-v1` from
[the digest spec](/spec/audio-integrity/) alone. The
[verification guide](/verify/#check-the-audio-match) shows how to download it
and compare the result with the claims in a file. For the downloadable example,
the computed digest and the stored claim agree:

```console
{{demo.audioDigest}}
```

The file contains {{demo.sampleCount}} playable samples at {{demo.sampleRate}} Hz,
for a duration of {{demo.durationMs}} ms. These values and the digest above are
read from the downloadable file when the site is generated.

## Checking your work

Use the [complete file-checking walkthrough](/verify/) for the downloads,
commands and interpretation of each result. It keeps the checks separate:
payload bytes, audio identity and shape, JSON validity, and the behavior of the
receiving application.

When implementing a producer, also review the cross-field rules: one default
per slot, valid `sourceTranscriptId` references, and agreement between the
manifest and summary tags. Passing a schema or the extractor's `--check` alone
does not establish those rules. The [normative producer requirements](/spec/v1/#writing-a-file)
remain the contract.
