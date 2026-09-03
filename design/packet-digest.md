# Why the audio digest is over Opus packets

Date: 2026-08-28

The first version hashed decoded PCM. Opus decoders are not bit-exact; the two
inside one ffmpeg binary disagree on the same file:

```console
$ ffmpeg -c:a opus    -i meeting.opus -f s16le … | sha256sum
995cf949d127f3b3c270c6f5…
$ ffmpeg -c:a libopus -i meeting.opus -f s16le … | sha256sum
8f1f52bf40dac2d9262d133f…
```

A digest over the audio packets is deterministic and survives reprocessing:

| operation | digest |
|---|---|
| original | `213e1a45…` |
| `ffmpeg -c copy` | `213e1a45…` |
| tag rewrite | `213e1a45…` |
| remux `.opus` → `.ogg` | `213e1a45…` |
| re-encode 48k | `36b3ebf3…` |

It is also 60× faster: 0.02 s against 1.22 s for decode plus hash.

A mismatch does not discard the transcript. The old rule did, and it fired on
every shipped file because the sample count was off by the 312-sample Opus
pre-skip. The reader keeps the transcript and labels it `unverified`; the
producer is where the strict check lives.
