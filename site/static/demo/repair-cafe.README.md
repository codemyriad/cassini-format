# The demo recordings

**Saturday repair café: the rain plan** is a scripted, AI-voiced planning call
between three fictional volunteers. Rain forces their Saturday repair café
indoors, but the hall isn't free until 10:30. They work through opening time,
bike bookings, table space and who needs to call whom.

- [Full Cassini file](repair-cafe.opus): about two minutes, three speakers.
- [Short excerpt](repair-cafe-excerpt.opus): the first scene, about 42 seconds.
- [Multitrack source recording](repair-cafe.multitrack.mkv): three separate,
  synchronized, lossless audio tracks, labelled Maya, Jonah and Tess.
- [Authored script](repair-cafe.script.json) and [production record](repair-cafe.production.json).

The public `.opus` files are produced by **Cassini itself** from the multitrack
recording. Their transcripts are its unedited speech-recognition output.
The script and external timing estimates are not supplied to Cassini.

## Generating the voices

[Eleven v3 Text to Dialogue](https://elevenlabs.io/docs/overview/capabilities/text-to-dialogue)
generated three continuous scenes using Alice as Maya, George as Jonah, and Lily
as Tess. Continuous dialogue preserves the model's phrasing across turns. These
are standard preset voices representing fictional people.

Four short acknowledgments were generated in separate takes with their
surrounding conversation as context. Only the acknowledgment audio was retained.
They are placed over the principal speaker's continuing phrase at a slightly
lower level: Tess's “Right,” Maya's “Yeah,” Jonah's “Mm-hmm,” and Tess's “Okay.”
The overlaps exist in the audio, before any transcription or rendering.

Main turns were separated at measured quiet boundaries into one synchronized
track per person. Each acknowledgment went onto its own speaker's track.
The three tracks sum back to the authored mix, within PCM quantization.
This uses the original, unmixed TTS takes; no source-separation model is involved.
The downloadable Matroska file contains three mono 24 kHz FLAC streams.

Scribe v2 recognition was used only to locate edits in the source takes and
check their spoken content. Long gaps between turns were shortened to varied
280–380 ms pauses. Within-turn hesitations remain. The opening of each scene is
preserved, and acknowledgment clips retain quiet handles to avoid cutting
consonants. Eleven v3's returned character timestamps were not used: they led
the speech by up to two seconds in these takes.

## Processing with Cassini

Cassini reads the three participant-labelled streams, mixes the listening
copy, recognizes each speaker separately, measures cross-track attribution,
and bounds word ends against that speaker's audio. The recipe uses its bundled
**Parakeet TDT 0.6B v3 fp32** recognizer through sherpa-onnx on CPU. Automatic
speaker-name hints are disabled for this example; optional summary generation
is off. Speaker identity comes from the source stream metadata.

Processing this source exposed a Cassini windowing bug: a VAD span contained
an acknowledgment, a long quiet gap and a later sentence. Fixed decoding windows
cut through that sentence and lost part of it. The included
[Cassini patch](https://github.com/codemyriad/cassini-format/blob/main/site/scripts/cassini-vad-silence.patch)
splits long VAD spans at sustained acoustic silence before applying the usual
windowing to continuous speech. The production record identifies the base
revision and patch, so this is a reviewable pipeline change.

Cassini then packs the listening copy and recognized words into each `.opus`
file. The site copies those exact bytes, without retagging or editing the
transcript. [Full transcript JSON](repair-cafe.words.json) and
[excerpt JSON](repair-cafe-excerpt.words.json) are decoded copies of their
embedded word items. The production record includes output hashes and the
recognizer/attribution provenance carried by the files.

Recognition and word boundaries are model estimates, not manual ground truth.
The script is available for comparison. The recognizer repeats “until” once
in the opening sentence; that small error is retained in both files. Cassini's
`provenance.wordTimings.endsBoundedByAudio` records its acoustic word-end check;
it does not promise perfect recognition or sample-accurate word starts.

## The transcript interface

The site mounts Cassini's actual `MeetingView` component, including its turn
reconstruction, inline interjections, individual word hover/seek targets and
playback highlighting. Both speakers' words can
highlight during an overlap. Word times come from the file, with no timing
interpolation in the player.

Upstream PR #229 unintentionally removed word interactions. The restoration is
tracked in [D-734](https://linear.app/code-myriad/issue/D-734/restore-word-level-transcript-highlighting-and-seeking-in-the-cassini).
This site uses that same Cassini implementation; its integration patch does
not add a separate word renderer or highlighting algorithm.

## Rebuilding

The scripts in `site/scripts/` require Python with `requests` and `numpy`, plus
`ffmpeg` and `ffprobe`. Voice generation and the editing reference use an
ElevenLabs key with text-to-speech and speech-to-text permissions. Normal site
builds make no AI API calls.

```bash
python3 site/scripts/synthesize-demo.py --cache /tmp/repair-cafe-tts --generate
python3 site/scripts/align-demo.py --cache /tmp/repair-cafe-tts
python3 site/scripts/produce-demo.py --cache /tmp/repair-cafe-tts --out /tmp/repair-cafe-tracks
```

Set `ELEVENLABS_API_KEY` in the environment before generation. A matching cache
avoids repeat API calls; changed inputs require a fresh cache. Review new takes
because the model's seed is best effort. The alignment step rejects unexpected
omissions or substitutions before the tracks are assembled.

Build Cassini from the revision in the production record in an isolated checkout,
with the included VAD patch applied. Then run the native pipeline:

```bash
site/scripts/process-demo-cassini.sh /path/to/cassini \
  /tmp/repair-cafe-tracks/repair-cafe.multitrack.mkv /tmp/repair-cafe.opus
```

For the excerpt, trim all three streams to the first scene before processing
and packing them with the same command. `publish-demo.py` copies reviewed native
outputs into the site and exports their embedded words and provenance; its
`--help` lists the required source and processing records. Finally run
`node site/scripts/gen-demo.mjs` to refresh the facts quoted by the pages.

## Earlier fixtures and licensing

The original [Lantern Festival notes](lantern-festival.README.md) and recordings
remain available for existing links. That older example used Kokoro-82M and
interpolated word timings. `elements.opus` powers the separate song karaoke demo.

The script, metadata and demo fixtures follow the repository's
[licensing terms](../../../LICENSE.md). Voice models are not included. Cassini's
component and the transcription patch are AGPL-3.0; the independent format
readers and producer remain CC0.
