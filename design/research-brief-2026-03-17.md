# Research Brief: Audio File Format With Embedded Transcription

Date: 2026-03-17

Prepared for: Format research expert

## What We Need

We want to formalize a file format that extends audio files with rich transcription metadata. The goal is a single file that:

1. Plays in any standard audio player (progressive enhancement)
2. Carries a full timestamped transcript that can seek the audio
3. Retains enough provenance and raw data to allow future reprocessing
4. Works across multiple use cases (meetings, lectures, songs with lyrics, etc.)

We have a working v1 implementation today. We want an expert to research the status quo of related formats and standards, then recommend the best path to formalize this into a proper, well-designed file format.

---

## Current Implementation (Cassini Portable Meeting v1)

### File shape

- Extension: `.opus`
- Container: Ogg
- Audio codec: Opus (48 kHz, mono or stereo)
- Metadata transport: OpusTags (Vorbis Comment fields in the Ogg Opus header)
- Structured payload: JSON, gzip-compressed, base64url-encoded, split across numbered OpusTags fields

A file looks like a normal `.opus` audio file to any audio player. Cassini-aware tools read the `CASSINI_FORMAT` tag, reconstruct the payload from `CASSINI_PAYLOAD_000..N` chunks, and get a full manifest.

### Metadata layers

**Layer 1 — Human-readable summary tags** (standard Vorbis Comment fields):

- `TITLE`, `DATE`, `DESCRIPTION`, `ENCODER`, `LANGUAGE`
- Plus Cassini-specific summary tags: `CASSINI_MEETING_ID`, `CASSINI_SPEAKER_COUNT`, `CASSINI_WORD_COUNT`, `CASSINI_TRANSCRIPT_LANGUAGE`, etc.

**Layer 2 — Structured payload** (compressed JSON manifest):

Descriptor tags tell consumers how to decode:

```
CASSINI_FORMAT=org.cassini.portable-meeting/1
CASSINI_PROFILE=ogg-opus
CASSINI_PAYLOAD_MIME=application/vnd.cassini.portable-meeting+json
CASSINI_PAYLOAD_ENCODING=base64url+gzip+utf8json
CASSINI_PAYLOAD_CHUNK_COUNT=<N>
CASSINI_PAYLOAD_SHA256=<hex>
CASSINI_DECODE_HINT=Concatenate CASSINI_PAYLOAD_000..N, base64url decode, gzip decompress, parse UTF-8 JSON.
```

### Manifest schema

The decompressed JSON payload conforms to a JSON Schema. Top-level structure:

```json
{
  "kind": "cassini-portable-meeting",
  "version": 1,
  "profile": "ogg-opus",
  "meeting": {
    "id": "mtg_<pcm-sha256>",
    "title": "Weekly Sync",
    "createdAtUtc": "2026-03-11T14:30:00Z",
    "durationMs": 3600000,
    "language": "en"
  },
  "audio": {
    "container": "ogg",
    "codec": "opus",
    "sampleRate": 48000,
    "channels": 1,
    "sampleCount": 172800000,
    "durationMs": 3600000
  },
  "integrity": {
    "matchPolicy": "exact-pcm",
    "pcmFormat": "s16le",
    "pcmSha256": "<hex>",
    "sampleRate": 48000,
    "channels": 1,
    "sampleCount": 172800000,
    "durationMs": 3600000
  },
  "speakers": [
    { "id": "speaker_0", "label": "Alice" },
    { "id": "speaker_1", "label": "Bob" }
  ],
  "transcript": {
    "format": "cassini.words.v1",
    "wordCount": 12345,
    "items": [
      { "speaker": "speaker_0", "startMs": 1200, "endMs": 1800, "text": "Hello" }
    ]
  },
  "provenance": {
    "speechToText": {
      "backend": "local-whisper",
      "engine": "faster-whisper",
      "model": "large-v3",
      "device": "cuda",
      "language": "en"
    },
    "readableCleanup": {
      "backend": "openai-compatible",
      "engine": "llama.cpp",
      "model": "cassini-cleanup-qwen35-0.8b-v35-q4km"
    }
  },
  "readableTranscript": { "...": "optional LLM-cleaned version" },
  "chapters": [{ "startMs": 0, "title": "Introduction" }],
  "summary": {},
  "attachments": []
}
```

### Integrity system

The format computes a SHA-256 hash of the decoded PCM audio (s16le, 48 kHz). If a consumer decodes the audio and gets a different hash, the transcript is treated as stale. This guards against someone editing the audio while leaving old metadata behind.

### Manual decode flow

Anyone can extract the transcript from the command line:

```bash
ffprobe -v error -show_entries format_tags:stream_tags -of json meeting.opus
# then: concatenate CASSINI_PAYLOAD_000..N, base64url decode, gzip decompress
```

---

## Design Principles We Want To Keep

### 1. Progressive enhancement

The file must be playable as plain audio by any player that supports the container format. Players that don't understand the metadata simply ignore it and play audio normally.

### 2. Information retention for future reprocessing

We keep multiple layers of the transcript to allow reprocessing later:

- **Raw ASR transcript** (`transcript`): The word-level output from speech-to-text, with per-word timestamps. This is the canonical source of truth.
- **Readable transcript** (`readableTranscript`): An LLM-cleaned version that removes filler words, adds punctuation, and improves readability. This is optional and derived.
- **Provenance metadata**: Which STT engine, model, device, and cleanup model produced each layer. This lets us know exactly what generated the data and decide whether reprocessing with a newer model would help.

The philosophy: if information can be retained that might enable better future processing, keep it. The raw ASR is always preserved even after cleanup, because a better LLM may come along.

### 3. Self-describing format

The metadata includes explicit encoding descriptors and a decode hint so that a curious observer can figure out the format without reading source code.

---

## Known Gaps and Desired Extensions

### Audio source map (new requirement)

When we mix multiple audio tracks into one (e.g., multiple meeting participants), we lose the information about which time ranges came from which source. We want to preserve a map like:

```
0:00 - 0:22  silence (no active speakers)
0:22 - 0:43  Channel "Alice"
0:43 - 0:55  Channel "Alice" + Channel "Bob" (overlap)
0:55 - 1:10  Channel "Bob"
```

This would help future diarization if we want to reprocess the STT. Today we have per-speaker audio tracks during processing, but this mapping is discarded when we produce the final mixed audio.

### Container flexibility

v1 is locked to Ogg Opus. We might want to support other containers (MP4/M4A, WebM, FLAC, MP3) for different use cases:

- Songs with lyrics might naturally be MP3 or FLAC
- Some platforms prefer M4A
- Lossless archival might want FLAC

The question: should the format be container-agnostic with container-specific "profiles", or should it define one canonical container?

### Use case breadth

v1 was designed for meeting recordings. We want the format to also cover:

- **Lessons / speeches / talks**: Single speaker or panel, possibly with slide markers
- **Songs with lyrics**: Timestamped lyrics synced to music, possibly with verse/chorus structure
- **Podcasts**: Multi-speaker, possibly with chapters and show notes
- **Audiobooks**: Chapter markers, narrator identification
- **Field recordings with annotations**: Timestamped notes synced to audio

Each use case may need slightly different metadata fields, but the core mechanism (audio + timestamped text + provenance) is shared.

### Richer transcript models

v1 stores a flat list of word-timed items. Future needs might include:

- Hierarchical structure (paragraphs > sentences > words)
- Confidence scores per word
- Alternative hypotheses
- Language tags per segment (for multilingual content)
- Phonetic/pronunciation data
- Non-speech event markers (applause, laughter, music)

### Capacity limits

The current approach of encoding everything in Ogg comment tags has practical limits. Very long meetings or very detailed metadata could push the payload size. We haven't hit this yet, but it's worth considering.

---

## Technical Context

### Pipeline overview

The Cassini pipeline works as follows:

1. **Record**: Capture multi-track audio from a meeting (one track per participant)
2. **Remux**: Produce a multitrack MKV with per-participant audio streams
3. **Transcribe**: Extract per-speaker audio (preserving sparse packet timing), run STT per speaker with word timestamps, remap to final audio timeline
4. **Silence compress**: Detect all-speaker silence, compress long gaps, produce a shorter digest audio
5. **Cleanup**: Optionally run an LLM to clean the raw ASR into readable text
6. **Pack**: Mix audio to mono Opus, build the manifest, embed in Ogg tags, verify integrity

### Transcript data flow

```
Per-speaker audio tracks
  -> STT (Parakeet / Whisper) -> word-timed segments per speaker
  -> Timeline remapping (source -> digest)
  -> Merge into canonical transcript (transcript.words.v1.json)
  -> LLM cleanup -> readable transcript (transcript.readable.v1.json)
  -> Both embedded in portable .opus file
```

### Viewer consumption

The web viewer extracts the manifest from the `.opus` file, reconstructs three transcript representations:

1. `transcript.words.v1.json` — canonical word-timed segments
2. `transcript.readable.v1.json` — LLM-cleaned paragraphs with source segment references
3. `transcript.display.v1.json` — display-ready blocks with token-level alignment to source words (allows click-to-seek on the cleaned text)

The display transcript uses LCS alignment to map cleaned text tokens back to source word timestamps, enabling click-to-seek even on text that was edited by the LLM.

### STT models in use

- **NVIDIA Parakeet** (CTC 0.6B): GPU-backed, direct word timestamps
- **Whisper** (large-v3, small.en): Via faster-whisper, various sizes
- Pipeline is model-agnostic: any HTTP STT endpoint that returns word-timed output

### LLM cleanup models

- Custom fine-tuned Qwen 2.5 models (0.8B-3B parameter range)
- Served via llama.cpp or Ollama locally
- Also supports OpenAI-compatible APIs and OpenRouter
- Current evaluation shows the fine-tuned model producing no-ops (100% exact copy rate), so this layer is actively being improved

---

## Rejected Alternatives (from v1 design)

| Alternative | Why rejected |
|---|---|
| ZIP-like `.cassini` package | Not directly playable in audio players |
| MP4/M4A with custom atoms | Harder to inspect from command line; less standard tooling for custom atoms |
| WebM audio | Less obviously "just an audio file" to users |
| Raw JSON in tags (no compression) | Unnecessary tag bloat |
| Single binary blob tag | Format would not be self-describing or inspectable |

---

## What We Want From The Expert

1. **Status quo research**: What existing standards and formats address timestamped text + audio? Consider:
   - Subtitle/caption formats (WebVTT, SRT, TTML, SSA/ASS)
   - Lyrics formats (LRC, SYLT in ID3, synchronized lyrics in various containers)
   - Podcast chapter standards (Podcasting 2.0, enhanced podcasts)
   - Audiobook formats (M4B, Audible)
   - Speech corpus formats (TextGrid, CTM, RTTM, Kaldi)
   - Multimedia containers with metadata (Matroska, MP4, Ogg)
   - MPEG-related standards (MPEG-4 Timed Text, MPEG-H)
   - Accessibility standards (WCAG, EBU-TT)
   - Any existing "audio + transcript in one file" formats we may not know about

2. **Gap analysis**: Where does our current approach sit relative to the state of the art? What do existing standards do better? What are we doing that nobody else does?

3. **Format recommendation**: Based on the research, recommend the best approach for our format. Consider:
   - Should we build on an existing standard or define our own?
   - Should we be container-agnostic or pick one container?
   - How should we handle the metadata transport across different containers?
   - How should versioning and extensibility work?
   - What MIME types and file extensions should we use?
   - How should we handle the different use cases (meetings vs. songs vs. lectures)?

4. **Specification structure**: What should a formal specification look like? What sections does it need? What conformance levels should it define?

5. **Ecosystem considerations**: What would adoption look like? How would this format interact with existing tools, players, and standards?

---

## Reference Materials

These files in the repository contain the full implementation details:

- Format specification: `PORTABLE_MEETING_FORMAT.md`
- JSON Schema: `spec/cassini-portable-meeting-manifest-v1.schema.json`
- Go manifest types and encoding: `cassini-go-recorder/internal/portable/manifest.go`
- Go packing implementation: `cassini-go-recorder/internal/cassini/portable_meeting.go`
- Go inspect/decode implementation: `cassini-go-recorder/internal/inspect/portable_audio.go`
- Transcriber architecture: `cassini-transcriber/docs/architecture.md`
- LLM cleanup pipeline: `cassini-transcriber/cassini_transcriber/llm.py`
- Viewer export and consumption: `cassini-viewer/scripts/export-static-meetings.mjs`
- Sparse stream timing: `cassini-transcriber/docs/sparse-stream-timing.md`
- Recording formats: `cassini-go-recorder/docs/formats.md`
- Muxing details: `cassini-go-recorder/docs/muxing.md`
