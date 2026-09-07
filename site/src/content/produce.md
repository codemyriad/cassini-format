The audio is ordinary Ogg Opus, so the only real work is building the tags.

If you would rather read code, there is [a complete producer in
standard-library Python](#a-complete-producer).

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
   | `CASSINI_PAYLOAD_SCHEMA` | `https://cassini-format.codemyriad.io/schema/cassini-portable-meeting-manifest-v1.schema.json` |
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
[the digest spec](/spec/audio-integrity/) alone. Run it against the file the
front page links to:

```bash
python3 tools/cassini-opus-digest.py lantern-festival.opus
ffprobe -v error -show_entries stream_tags=CASSINI_AUDIO_OPUS_SHA256 \
        -of default=nw=1:nk=1 lantern-festival.opus
```

```console
{
  "sha256": "8e1f7499c6d5fba88c3bd9b69ecd3de1b07ae0cff65152c942c5e99062d01cbc",
  "sampleRate": 48000,
  "channels": 1,
  "sampleCount": 11506248,
  "durationMs": 239713,
  "packetCount": 11986
}
8e1f7499c6d5fba88c3bd9b69ecd3de1b07ae0cff65152c942c5e99062d01cbc
```

Two implementations that never saw each other's code, in two languages, agree
on all 64 characters over 11,986 packets.

## Checking your work

```bash
# still a playable Opus file. If this fails, nothing else matters.
ffmpeg -v error -i meeting.opus -f null -

# the manifest and the transcript body decode and validate
python3 tools/cassini-extract.py meeting.opus > manifest.json
python3 tools/cassini-extract.py meeting.opus --transcript > body.json
python3 -c "import json,jsonschema
v = lambda d, s: jsonschema.validate(json.load(open(d)), json.load(open(s)),
                                     format_checker=jsonschema.FormatChecker())
v('manifest.json', 'spec/cassini-portable-meeting-manifest-v1.schema.json')
v('body.json', 'spec/cassini-words-v1.schema.json')"

# the tags mirror the manifest, and the audio digest is the one in the file
python3 tools/cassini-extract.py meeting.opus --check
python3 tools/cassini-opus-digest.py meeting.opus

# an independent reader agrees with you
python3 tools/cassini-read-pure.py meeting.opus
```

The schemas check shape. The cross-field rules, one default per slot, a
`sourceTranscriptId` that names a declared transcript, `integrity` equal to
`audio`, are prose, and `--check` is where they are tested. With gocassini
built, `cassini inspect meeting.opus` is the last check, and the one that
catches a disagreement between your digest and the reference one.
