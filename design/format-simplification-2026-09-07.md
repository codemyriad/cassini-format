# Format audit against Cassini main

Date: 2026-09-07

Compared against fetched gocassini `origin/main`, commit
[`e4856e9fac32c447d6c5e023681433319d7ea3c8`](https://github.com/codemyriad/gocassini/tree/e4856e9fac32c447d6c5e023681433319d7ea3c8).
The local Cassini checkout was behind at `7774ed1`; it was not used as the
comparison target. The matching implementation is
[Cassini PR 276](https://github.com/codemyriad/gocassini/pull/276).

The main simplification is to stop classifying the origin of word-timed text.
The words, their body format, the selected default and optional processing
provenance already describe what a reader needs. Requiring a label buys only
extra validation and special cases.

## Removed from the current contract

| Feature | Evidence on the pinned main | Change |
|---|---|---|
| Word-transcript `role` and `sourceTranscriptId` | Go and the viewer validate an origin enum. The normal writer hardcodes `raw-asr`; authored-text labels are fixture metadata. No production correction or translation workflow was found. | Word entries need `id`, `format`, `payloadRef`; defaults and array order select them. Ignore old origin labels and links. |
| `readable-cleanup` and `provenance.readableCleanup` | `manifest.go` calls the role withdrawn; the cleanup producer has been deleted. Go explicitly skips older entries. | Remove the current cleanup slot and provenance definition. Keep old entries skippable. |
| `chapters` | Go has a struct and JSON round-trip plumbing, but no portable writer populates it. The viewer's optional `chapters.vtt` sidecar is separate. | Remove the manifest field and chapter schema. |
| `meeting.summary` | The Go field's comment says it is reserved, left empty, and has no requested meaning. The writer stores real summaries in `summary.md`. | Remove this unused second place for summary content. |
| `meeting.language` | The production manifest builder never sets it. Transcript language and processing-step language already exist. | Remove the meeting-level declaration; keep transcript and processing language. |
| `meeting.roomName` / `CASSINI_ROOM_NAME` | Already removed from the Go meeting struct and writer; the current room name belongs in the catalog. | Remove the current declaration and mirror tag. Old members follow the unknown-member rule. |
| `payloads` / `CASSINI_PL_` | A future reservation in this spec, with no writer or reader implementation found. | Remove the reservation. |

Implementation evidence:

* [Go manifest types and validation](https://github.com/codemyriad/gocassini/blob/e4856e9fac32c447d6c5e023681433319d7ea3c8/cassini-go-recorder/internal/portable/manifest.go).
* [Transcript encoding, validation and defaults](https://github.com/codemyriad/gocassini/blob/e4856e9fac32c447d6c5e023681433319d7ea3c8/cassini-go-recorder/internal/portable/manifest_transcripts.go).
* [Production manifest construction](https://github.com/codemyriad/gocassini/blob/e4856e9fac32c447d6c5e023681433319d7ea3c8/cassini-go-recorder/internal/cassini/portable_meeting.go).
* [Production transcript assembly](https://github.com/codemyriad/gocassini/blob/e4856e9fac32c447d6c5e023681433319d7ea3c8/cassini-go-recorder/internal/cassini/portable_meeting_tags.go).
* [Viewer validation and selection](https://github.com/codemyriad/gocassini/blob/e4856e9fac32c447d6c5e023681433319d7ea3c8/cassini-viewer/src/viewer/portable.ts).

The current source and checked-in proposals were searched for writers and
consumers. An unused type or an old design's hypothetical use case was not
counted as an implemented feature. This cannot establish plans outside the repo.

## Kept because Cassini uses it

| Feature | Current use |
|---|---|
| Multiple transcripts, ids and default selection | The producer packs additional model passes; the viewer switches among them and gets labels from ids and provenance. |
| `readableTranscripts`, `role: "display"`, `sourceTranscriptId` | The producer packs native `transcript.display.v1` blocks. The viewer needs the source link to pick the matching display when switching transcripts. |
| `provenance.speechToText` and `displayTranscript` | Per-pass model descriptions and display processing records. |
| Attribution fields and `provenance.wordTimings` | The pipeline records crosstalk evidence; timing provenance controls whether a consumer repairs word ends. Removing it changes behavior. |
| Top-level `summary`, attachments and summary provenance | Real `summary.md` content and its generation metadata are packed and read. |
| Room id, job id, attempt number, recording and processing times | Actual operator output and artifact identity. |
| Chunk descriptors, independent bodies and audio integrity | The readers validate these and use the audio digest to bind metadata to the recording. |
| `x` private metadata | The site's synthetic demo records how its audio and timings were made here. |

Some duplication could be removed in a larger wire revision: `audio` versus
`integrity`, constant profile/codec/rate tags, MIME and encoding descriptors,
and word counts. Current code uses or validates these. They are not removed
by this pass. The ten reserved transcript ids are also enforced by the Go
writer and validator; their stated namespace-collision rationale is dubious
because transcript chunks already live under `CASSINI_TX_`, but removing that
restriction can be handled separately.

## Compatibility and Cassini follow-up

The new readers still accept existing word transcripts with origin labels.
Historical drafts and the original conformance vectors are kept as such.
The new producer and demos omit the label. The audio and payload transport
retain their existing format ids.

The audited main rejected a word entry with no `role`. The
[Cassini follow-up](https://github.com/codemyriad/gocassini/pull/276) implements
these changes:

1. Go and browser validators ignore word origin labels and source links,
   including non-string legacy values. Display source and payload validation
   remain.
2. Build-artifact readers ignore legacy word roles; new build artifacts and
   portable output omit them. The internal encoder distinguishes only words
   from display documents. Existing `raw-asr` ids stay stable and opaque.
3. The static exporter follows the same rules as the viewer. Unsupported
   readable roles, including withdrawn cleanup, are skipped without loading
   their bodies. Displays are selected by source, then default, then array order.
4. The vendored schema and format guide match the public contract. Unused Go
   chapter and meeting-hint fields are removed.

Readers continue accepting older files. Installed Cassini versions that predate
this follow-up need an update to open newly produced files without `role`;
merging source changes does not upgrade an installed ExApp.

The display body correction is separate from origin labels: the old spec
incorrectly called every body `cassini.words.v1`, even though Cassini writes
and reads native display blocks. The current spec now reflects that behavior.

## Validation

The JavaScript reader and both Python extractor profiles have zero failures
across 26 vectors. The four new vectors cover omitted/unknown origin labels,
second-default selection, and a native display beside an unavailable withdrawn
cleanup entry. Schemas validate the new files. The original 22 vectors retain
legacy metadata for compatibility coverage.

Cassini validation: recorder `go test -race ./...` and `go vet ./...`; 428 viewer
tests and 99 app tests; standalone and embedded builds. Tests cover legacy
build-artifact input through packing, non-string ignored metadata, display
source validation and selection, transcript switching and crosstalk mapping.

The updated Go binary passes all four new vectors. Across the full suite it has
18 passes, 7 advisory warnings and one failure: 011, where it rejects a
tag/manifest audio-digest disagreement instead of using the manifest. That
failure was reproduced on the pinned starting main and predates this change.
The old main also rejected 023–025 for their missing/unfamiliar roles; its viewer
showed the same errors. Those origin-label failures are resolved by the follow-up.

The site passes type checking and a production build, with existing CSS and
accessibility warnings. All three tracked demos validate; their audio packets
and word bodies match the previous files exactly.

An independent `agy --dangerously-skip-permissions` review identified the static
exporter, legacy build-input compatibility, and missing display/cleanup coverage.
Those paths are included in the implementation and regression checks above.

The final review confirmed those fixes and explicitly agreed to merge after CI,
with no blocking defects. The review record is attached to
[Cassini PR 276](https://github.com/codemyriad/gocassini/pull/276).
