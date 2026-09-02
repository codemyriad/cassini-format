The audio is ordinary Ogg Opus, so the only real work is building the tags. What
follows is what a real file contains, measured rather than quoted.

If you would rather read code, there is [a complete producer in about 200 lines
of standard-library Python](#a-complete-producer).

## What you are making

An Ogg Opus file at 48 kHz, mono for speech, with two things in its OpusTags
comment header: plain comments a human can read, and a JSON manifest gzipped,
base64url-encoded and cut into numbered pieces. Nothing else.

## Requirements

1. Container **MUST** be Ogg, codec **MUST** be Opus, sample rate field
   `48000`. Mono for speech; stereo only when it is deliberate.

2. **MUST** carry `CASSINI_FORMAT=org.cassini.portable-meeting/1`. That is what
   makes it a Cassini file.

3. **MUST** carry every descriptor tag:

   | tag | value |
   |---|---|
   | `CASSINI_FORMAT` | `org.cassini.portable-meeting/1` |
   | `CASSINI_PROFILE` | `ogg-opus` |
   | `CASSINI_PAYLOAD_MIME` | `application/vnd.cassini.portable-meeting+json` |
   | `CASSINI_PAYLOAD_ENCODING` | `base64url+gzip+utf8json` |
   | `CASSINI_PAYLOAD_SCHEMA` | the manifest schema URL |
   | `CASSINI_PAYLOAD_CHUNK_COUNT` | decimal integer |
   | `CASSINI_PAYLOAD_SHA256` | lowercase hex, over the **decompressed** JSON |
   | `CASSINI_PAYLOAD_RAW_BYTES` | decimal integer |
   | `CASSINI_PAYLOAD_GZIP_BYTES` | decimal integer |
   | `CASSINI_AUDIO_SAMPLE_RATE` | `48000` |
   | `CASSINI_AUDIO_CHANNELS` | `1` or `2` |
   | `CASSINI_AUDIO_SAMPLE_COUNT` | normalised playable samples |
   | `CASSINI_AUDIO_DURATION_MS` | `sampleCount * 1000 / 48000`, truncating |
   | `CASSINI_AUDIO_MATCH_POLICY` | `exact-opus-audio-v1` |
   | `CASSINI_AUDIO_OPUS_SHA256` | lowercase hex, the audio digest |
   | `CASSINI_DECODE_HINT` | one sentence explaining the chunk sets |

4. Build the payload in this order: compact UTF-8 JSON, gzip, base64url
   **without padding**, split. Getting the order wrong is the commonest way to
   produce a file nothing can read.

5. Chunks **MUST** be `CASSINI_PAYLOAD_NNN`, zero-padded to a *minimum* of
   three digits, from `000`, joined by index with no separator, exactly
   `CHUNK_COUNT` of them. Index 1000 is `CASSINI_PAYLOAD_1000`, not truncated
   and not four-padded from the start. Keep each value at or under 4096
   characters. Not an Ogg requirement; it keeps the header readable in ordinary
   tools.

6. Both SHA-256s are over **decompressed** bytes, not the gzip stream and not
   the base64 text.

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

10. **At most one** entry flagged `default: true` per slot — one across the
    word-timed roles, one across `readable-cleanup`, one across `display`.
    Flagging none is legal and readers fall back to array order.
    `CASSINI_TRANSCRIPT_DEFAULT` mirrors the words slot. A derived transcript
    carries `sourceTranscriptId`.

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
    nothing and a new producer may as well.

13. Verify your own output before shipping it: read it back, recompute both
    digests, refuse to publish a mismatch. The producer is the right place for
    the strict check, because it can fix the problem and a reader cannot.

14. Keep the raw ASR transcript even when a cleaned version exists. A better
    cleanup model is coming and it will want the original.

## Conventions

Not required. All of it is what the reference producer does.

* **Write `TITLE`, `DATE` and a `DESCRIPTION`** saying in one line how to decode
  the payload. They cost nothing and they are what somebody sees on right-click.

* **Do not bother with `ENCODER`.** The producer sets `Cassini`, ffmpeg's Ogg
  muxer overwrites it with `encoder=Lavf…`. So nothing in a Cassini file records
  which program wrote it, which is the omission I would most like back.

* **Write a summary tag only when you have a value.** An empty
  `CASSINI_ROOM_ID` reads as "this meeting has a room whose id is the empty
  string". Absent, never empty.

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

That is easier than what the reference implementation does. Since the digest
excludes `OpusTags` *and* all Ogg framing, tagging provably cannot change it, so
there is no hash-tag-rehash loop. Compute it once.

`tools/cassini-opus-digest.py` is ninety lines computing `exact-opus-audio-v1`
from [the digest spec](/spec/audio-integrity/) alone. Run it against the file the
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

Two implementations that never saw each other's code, two languages, the same 64
characters over 11,986 packets. That is the only evidence I have that the digest
rule is written down properly, and it is worth more than my opinion.

## Checking your work

```bash
# still a playable Opus file. If this fails, nothing else matters.
ffmpeg -v error -i meeting.opus -f null -

# the manifest decodes and validates
python3 tools/cassini-extract.py meeting.opus > manifest.json
python3 -c "import json,jsonschema; jsonschema.validate(
  json.load(open('manifest.json')),
  json.load(open('spec/cassini-portable-meeting-manifest-v1.schema.json')))"

# an independent reader agrees with you
python3 tools/cassini-extract.py meeting.opus --tags
python3 tools/cassini-extract.py meeting.opus --list
```

With gocassini built, `cassini inspect meeting.opus` is the fourth check, and the
one that catches a disagreement between your digest and the reference one.
