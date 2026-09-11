# Final Moments in Cassini Mission Control

**Courtesy NASA/JPL-Caltech.** Recorded September 15, 2017.
[Original video and JPL transcript](https://www.jpl.nasa.gov/videos/final-moments-in-cassini-mission-control/).
The audio is used under the [JPL image use policy](https://www.jpl.nasa.gov/jpl-image-use-policy/),
not the repository’s CC0 dedication. NASA, JPL and Caltech do not endorse this project.
The transcript is our AI-assisted reconciliation, not an official NASA transcript.

- [Download the Cassini recording](cassini-final-moments.opus): the full 65-second stereo audio, including applause.
- [Word-timed transcript](cassini-final-moments.words.json).
- [Production record](cassini-final-moments.production.json): source hash, models, attribution and editorial decisions. This record is also embedded in the audio file.
- [Transcription comparisons](cassini-final-moments.evidence.json): model outputs and acoustic timing evidence, including unsuccessful attempts.
- [Closed captions extracted from JPL’s video](cassini-final-moments.captions.srt).

## How the transcript was reconciled

Independent full-audio passes used **Gemini 3.5 Flash**, **Gemini 3.8 Flash** and
**OpenAI GPT Audio** through OpenRouter, plus **ElevenLabs Scribe v2** with word
timing and diarization. They were asked to transcribe the audio without being
supplied JPL’s transcript. GPT Audio initially returned an acknowledgment;
its retry produced a transcript. Gemini 3.8’s first response was incomplete;
a retry with lower reasoning effort completed it. These attempts remain in the
comparison record. Normal site builds make no AI calls.

The outputs were compared with JPL’s webpage transcript and the video’s embedded
EIA-608 captions. The captions resolve a webpage error: the opening is
“transition to high rate mode,” not “condition high rate mode.” Scribe’s acoustic
word boundaries supply the seek targets; the general audio models’ segment
timestamps drift substantially and were rejected. A separate ElevenLabs forced-alignment request was attempted, but the key
lacks the `forced_alignment` permission. No forced-alignment result was used.
These are Scribe model estimates, not independently verified word boundaries.

The 9–13-second radio passage was also isolated, band-pass filtered at 150–3500 Hz,
and amplified for separate passes through all three audio models. The listening
copy contains the original, unfiltered stereo audio throughout.

## Speakers and uncertainty

**Julie Webster** and **Earl Maize** are explicitly identified in JPL’s transcript
and captions. Webster’s short call to the project manager and Maize’s “Go ahead”
are assigned using Scribe’s voice grouping and the exchange’s continuity.
**ACS 1** and the other **mission-control operator** retain role-based labels:
we could not substantiate their personal names. Model guesses are not identity evidence.

At **11.18–12.50 seconds**, after “We have loss of signal at,” JPL itself marks
unintelligible speech. Models variously propose X-band or X-ray band, followed
by S-band, Sierra band, C-band, Z-band or “zero band.” The transcript retains
**[unintelligible]** instead of publishing one guess as fact.

The published text retains “Okay,” the individually spoken time digits
“one one five five four six,” audible “uh” fillers, “Maybe a trickle,”
“within the next” and “gonna.” Around 27–28 seconds the models disagree about
quiet words between “but” and “just heard”; the conservative Scribe/GPT Audio
reading is retained. See the production record for the reconciliation decisions.
Applause remains audible at the end; it is not attributed to an individual speaker.
Unspoken closing-credit captions are not included as dialogue.

## Rebuilding

Download the original video using the URL in the production record, then run:

```bash
python3 site/scripts/produce-cassini-final.py /path/to/source.m4v
node site/scripts/gen-demo.mjs
```

The script checks the source SHA-256, encodes the full audio to stereo Opus,
and uses the repository’s standalone producer to embed the reviewed timed words,
source credit and production record. Packing verifies that the Opus audio digest
is unchanged by adding metadata. The original AAC is transcoded once; this is
not a claim of bit-identical audio to the source video.

## Earlier examples

The [repair café production notes](repair-cafe.README.md),
[repair café recording](repair-cafe.opus),
[short excerpt](repair-cafe-excerpt.opus), and
[Lantern Festival notes](lantern-festival.README.md) remain available.
Those fictional fixtures retain their original licensing and production history.
`elements.opus` powers the separate song karaoke demo.
