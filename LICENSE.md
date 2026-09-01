# Licensing

Freeze item 7: a spec licensed AGPL-3.0 is a standard nobody can safely
implement. So this repository is split three ways.

| what | licence | file |
|---|---|---|
| spec prose: `SPEC.md`, `CHANGELOG.md`, `README.md`, `design/*`, `site/src/content/*` | CC-BY-4.0 | [LICENSE-CC-BY-4.0.txt](LICENSE-CC-BY-4.0.txt) |
| schemas, examples and test vectors: `spec/*.json`, `spec/examples/*` | CC0-1.0 | [LICENSE-CC0-1.0.txt](LICENSE-CC0-1.0.txt) |
| the byte-and-JSON layout documents: `spec/cassini-opus-audio-integrity-v1.md`, `spec/cassini-words-v1.md` | CC0-1.0 | see below |
| reference code, meant to be copied: `tools/*` | CC0-1.0 | |
| the demo files: `site/static/demo/*` | CC0-1.0 | test vectors; see below |

The two layout documents are prose, but they are CC0 with the schemas rather
than CC-BY with the prose, because an implementer should be able to transcribe
an algorithm or a field table without an attribution obligation.

The demo files are test vectors that happen to be listenable. Their content is
synthetic: a fictional meeting from
[gocassini](https://github.com/codemyriad/gocassini)'s test harness, read by
[Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) (Apache-2.0, no
attribution obligation on model output). The fixture is relicensed here from its
AGPL-3.0 home by the same author, deliberately, so that a conformance vector
carries no licence question. `site/static/demo/README.md` records how they were
made.

The Cassini implementation stays AGPL-3.0 in
[gocassini](https://github.com/codemyriad/gocassini). Nothing here changes that.

## Patent non-assertion

No patent claims are asserted against implementations of this format. If that
ever needs to be a real legal instrument rather than a sentence, it should be
replaced with the [W3C Software and Document Notice and
License](https://www.w3.org/copyright/software-license/) or an equivalent.

## The name is not the product

"Cassini" is the name of a meeting recorder. Whatever this format ends up
called, that name identifies the format and does not imply endorsement by, or
affiliation with, the Cassini project or its authors. Implementations may state
that they read and write the format; they may not use the product name to
describe themselves.
