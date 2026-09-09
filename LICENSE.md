# Licensing

A specification licensed AGPL-3.0 is a standard nobody can safely implement.
The format and reference readers therefore have separate licenses from the
Cassini application component used to demonstrate them.

| what | licence | file |
|---|---|---|
| spec prose: `SPEC.md`, `CHANGELOG.md`, `README.md`, `design/*`, `site/src/content/*`, `spec/drafts/*.md` | CC-BY-4.0 | [LICENSE-CC-BY-4.0.txt](LICENSE-CC-BY-4.0.txt) |
| schemas, drafts' schemas, and the conformance suite: `spec/*.json`, `spec/drafts/*.json`, `spec/conformance/**` | CC0-1.0 | [LICENSE-CC0-1.0.txt](LICENSE-CC0-1.0.txt) |
| the byte-and-JSON layout documents: `spec/cassini-opus-audio-integrity-v1.md`, `spec/cassini-words-v1.md` | CC0-1.0 | see below |
| reference code, meant to be copied: `tools/*`, and the site's code under `site/` other than its content and the viewer exceptions below | CC0-1.0 | |
| Cassini viewer source, models, tests and license notices: `site/src/lib/vendor/cassini-viewer/**` | AGPL-3.0 | [upstream license](site/src/lib/vendor/cassini-viewer/LICENSE) |
| Cassini viewer embedding, generated viewer stylesheet and source-sync patch: `site/src/lib/viewer/**`, `site/scripts/sync-viewer.mjs` | AGPL-3.0 | same license; see [component provenance](site/src/lib/vendor/cassini-viewer/README.md) |
| Cassini transcription fix: `site/scripts/cassini-vad-silence.patch` | AGPL-3.0 | same upstream license; patch against the revision recorded in the demo production record |
| the demo scripts, metadata and audio: `site/static/demo/*` | CC0-1.0 to the extent of the author's rights | test vectors; see below |

The two layout documents are prose, but they are CC0 with the schemas rather
than CC-BY with the prose, because an implementer should be able to transcribe
an algorithm or a field table without an attribution obligation.

The meeting demos are scripted, fictional conversations with synthetic voices.
The earlier Lantern Festival fixture was made with Kokoro-82M and came from
[gocassini](https://github.com/codemyriad/gocassini)'s test harness; the same
author released that fixture here under CC0. The repair café conversation was
written for this site and generated with Eleven v3. The author's CC0 dedication
covers the scripts, metadata and generated audio to the extent the author holds
rights in them. It does not license third-party voice models, model weights,
voices or services. [The production notes](site/static/demo/README.md) identify
the models, voices, timing and editing used for each example.

The Cassini implementation stays AGPL-3.0, including the component vendored into
this website. Its source and license are available through the site's footer.
The standalone browser reader (`site/src/lib/reader/cassini.ts` and
`tools/cassini-read.js`), schemas and format algorithms remain CC0; an
implementation of the format need not use the AGPL viewer.

## Patent non-assertion

This is a statement of intent, not a licence: no patent claims are asserted
against implementations of this format. If it ever needs to be a real legal
instrument, it should be replaced with the [W3C Software and Document Notice and
License](https://www.w3.org/copyright/software-license/) or an equivalent.

## The name is not the product

"Cassini" is the name of a meeting recorder. Whatever this format ends up
called, that name identifies the format and does not imply endorsement by, or
affiliation with, the Cassini project or its authors. Implementations may state
that they read and write the format; they may not use the product name to
describe themselves.
