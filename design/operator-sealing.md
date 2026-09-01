# How the operator guarantees the file exists

Moved out of the specification: this describes how the Cassini operator
produces and hands off portable meeting files, not what a portable meeting file
*is*. Another producer could do this completely differently and still emit
conforming files. It is kept because the failure it fixes is easy to repeat.

This section says what makes
the operator's copy of it trustworthy, because for a long time it was not: the
`.opus` was packed by a background task started after the recording had already
been handed off for publishing, so it could fail, be killed by a restart, or be
overtaken by a rerun writing the same path — and none of that failed the job.

Sealing is now a stage the job has to pass, and everything downstream is bound to
the artifact it produced:

```text
  build            attempt .meeting bundle
    │
  SEAL             cassini pack  ->  runs/<job>--attempt-NNN.seal/<jobID>.opus
    │                  │  pack verifies its own output: it parses the packed
    │                  │  file and compares its compressed-audio SHA-256 and shape
    │                  │  against the manifest
    │                  │  it embedded, so a zero exit means packed AND checked
    │                  ▼
    │              sha256(file)  ────────────┐  the sealed digest
    │                  │                     │
    │              promote (atomic rename)   │
    │                  ▼                     │
    │              current/<jobID>.opus      │
    │                                        │
  PUBLISH          re-check sha256 ──────────┤  before anything is spawned
    │                  ▼                     │
    │              cassini publish <sealed .opus>  (verified, then copied
    │                  ▼                      through byte for byte)
  DELIVER          re-check sha256 of the staged copy ──┘
                       ▼
                   commit asset, then catalog LAST
```

Three properties follow, and each is worth stating on its own:

- **A publish cannot exist without a seal.** The only transition into
  `publish/queued` writes the sealed artifact's path and digest in the same
  database transaction.
- **The artifact is immutable and attempt-scoped.** A rerun seals its own file;
  it never rewrites the one a queued publish is about to deliver.
  `current/<jobID>.opus` is a promotion of a sealed artifact — a hard link where
  the filesystem allows one — not an independent pack of the same meeting.
- **The file that reaches the viewer is the file that was sealed.** The digest is
  a SHA-256 of the container bytes. That is a different question from
  `integrity.opusAudioSha256`, which hashes canonical compressed audio, survives
  a metadata-only remux, and is what a fresh v3 meeting id is derived from;
  both are kept because they answer
  different questions — "is this the same recording?" and "is this the same
  file?".
