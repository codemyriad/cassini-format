# The demo files

`lantern-festival.opus` is a real `org.cassini.portable-meeting/1` file. It is
what the site's front page reads, and what the numbers quoted around the site
come out of. `lantern-festival-excerpt.opus` is the first stretch of the same
meeting, for anything that wants a smaller file.

| file | bytes | duration | speakers | words | OpusTags comments |
|---|---|---|---|---|---|
| `lantern-festival.opus` | 1,898,861 | 239,713 ms | 6 | 669 | 37 |
| `lantern-festival-excerpt.opus` | 356,885 | 44,813 ms | 6 | 136 | 35 |

```
sha256(lantern-festival.opus)          a42b090be33c483a1e29ff1c3a7b93f46094f8a8794430b216b7878ec718c6b3
sha256(lantern-festival-excerpt.opus)  544339473ebae816bfe4c4e854e685995fd00bd7ddcdfe8bc42b0613c4df603f

meeting id, full     mtg_8e1f7499c6d5fba88c3bd9b69ecd3de1b07ae0cff65152c942c5e99062d01cbc
meeting id, excerpt  mtg_7ffa3ecfdaad5c6dc14e2b93c9a25073eb53b18ae512071afd650ef0f81fd3ad
```

The excerpt is a different meeting id because it is different audio: the meeting
id *is* the audio digest.

Nothing in either file came from a real meeting. The people, the company, the
festival and the artifacts are invented, and the URLs use the reserved
`.example` TLD.

## How they were made

The script is `showcase-lantern-festival.v1.json`, a fixture from
[gocassini](https://github.com/codemyriad/gocassini)'s test harness, written to
sound like a real meeting: interruptions, corrections, dates, filenames, issue
numbers and action items. A copy of the scenario as used here is next to these
files as `lantern-festival.scenario.json`.

1. Each of the six parts was rendered to speech with
   [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M), one voice per
   speaker, on CPU. About ten minutes on 24 cores; no GPU.

   ```bash
   UV_PYTHON=3.12 ./harness/bin/prepare-synthetic-meeting.sh \
     --scenario ./lantern-festival.scenario.json \
     --output-dir /tmp/kokoro-retimed --backend kokoro --force
   ```

2. The turn schedule was reflowed, because synthesised speech does not take the
   same time the fixture's placeholder timing assumed, and the original starts
   would have overlapped. The fixture's `start_seconds` were tuned against the
   harness `mock` backend, which emits exactly `max(1.2, words * 0.26)` seconds
   of tone per turn. Real speech runs 1.34x longer, which turns the author's
   nine deliberate short overlaps into thirty-two totalling 54 s, one of them
   6.8 s of two people saying different things. So each start was recomputed to
   keep the interval to the previous turn — gap or deliberate overlap — exactly
   as written:

   ```
   offset[i]    = old_start[i] - (old_start[i-1] + mock_dur[i-1])
   new_start[i] = new_start[i-1] + measured_dur[i-1] + offset[i]
   ```

   That restores the authored 9 overlaps / 7.37 s / 1.88 s max, and stretches
   the meeting from 182 s to 239.7 s. The result is
   `lantern-festival.scenario.json`. Kokoro is deterministic: two renders of the
   same 37 turns gave identical durations, so the reflow lands exactly.

3. The six tracks were mixed to one mono 48 kHz Opus program at 64 kbps, using
   the same filter the production pipeline uses
   (`cassini-go-recorder/internal/transcribe/audio.go`):

   ```bash
   ffmpeg -y -v error \
     -i mira.ogg -i leo.ogg -i ben.ogg -i ana.ogg -i noah.ogg -i jules.ogg \
     -filter_complex "[0:a][1:a][2:a][3:a][4:a][5:a]amix=inputs=6:duration=longest:normalize=0,alimiter=limit=0.95[out]" \
     -map "[out]" -ac 1 -ar 48000 -c:a libopus -b:a 64k -vbr on \
     -compression_level 10 -application voip \
     lantern.meeting/meeting.webm
   ```

   The excerpt is the same command plus `-t 44.81`. That cut sits in the silence
   after Jules ends at 44.67 s and before Mira starts at 44.83 s, so no audible
   turn is missing from its transcript and no transcribed turn is cut mid-word.

4. The transcript was built from the renderer's own schedule and the file was
   packed. Packing both takes under three seconds.

   ```bash
   cassini pack ./lantern.meeting --out ./lantern-festival.opus \
     --title "Lantern Festival Booth Run-through"
   ```

Every timestamp in these files is a constant, not a clock read. `DATE`,
`CASSINI_CREATED_AT` and `CASSINI_PROCESSED_AT` are all `2026-04-15T09:12:00Z`;
`CASSINI_RECORDED_AT_LOCAL` is `2026-04-15T11:12:00`, the same instant in
Europe/Berlin. Wednesday 15 April 2026 is a deliberate fictional date: the
meeting discusses "Friday, April seventeenth", two days later.

The bundles were built by hand with no room token, room name, job id or attempt
number, so neither file carries `CASSINI_ROOM_ID`, `CASSINI_ROOM_NAME`,
`CASSINI_JOB_ID`, `CASSINI_ATTEMPT_NUMBER`, or any `baseUrl` or `host` in
provenance. That is why the full file has 37 comments where an
operator-produced file has 38.

## What is measured and what is not

This matters, because the format's whole pitch is word-level timing and it would
be dishonest to demo it with numbers that were invented.

* **Measured:** every segment's start and end. Those come from the renderer's
  schedule for that speaker's own track, so they are exact.
* **Derived:** every individual word's start and end. They are interpolated
  inside their segment, proportionally to token length.

No speech-to-text ran at any point. The words are the script, verbatim, so the
one transcript in each file has id `script` and role `scripted`: authored text
the recording was made from, not a guess at it. `CASSINI_TRANSCRIPT_DEFAULT`
and `CASSINI_TRANSCRIPT_IDS` say `script`, and the body sits under
`CASSINI_TX_SCRIPT_PAYLOAD_*`.

The manifest carries no `provenance.speechToText`, because none ran. How the
fixture was built (renderer, voices, which timings are measured) is recorded
under the private-use member, `x["cassini-format.codemyriad.io"].fixture`, as a
processing step. `provenance.wordTimings` is deliberately absent, which is how
the format says "nobody measured these".

## Licence

CC0-1.0, as test vectors, per [LICENSE.md](../../../LICENSE.md). A conformance
vector should carry no licence question.

The audio was generated with [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M),
whose weights are Apache-2.0 and which places no condition on model output. Its
model card lists per-voice attribution only for its Japanese and French voices;
the six used here are American and British English and carry none. Credited
anyway.

## Regenerating

If you replace these files, re-run the site's fact generator so the pages stop
quoting the old ones:

```bash
node scripts/gen-demo.mjs
```
