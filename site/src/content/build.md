<!-- TODO(chris): wording -->
Everything here works on an ordinary `.opus` file. The readers and the producer
are standalone: copy one into your project, or use it to check what you built.

| Tool | What it does | Language | Licence | Link |
| --- | --- | --- | --- | --- |
| Browser reader | Opens a file and plays it with its transcript, without installing anything | JavaScript | CC0 reader, AGPL-3.0 transcript component | [Open a file](/try/) |
| `cassini-read-pure.py` | Reads a file with no external tools; parses the Ogg container itself | Python, stdlib only | CC0 | [tools/](https://github.com/codemyriad/cassini-format/blob/main/tools/cassini-read-pure.py) |
| `cassini-extract.py` | Prints the tags, the manifest or one transcript; `--check` verifies the payload digests | Python + ffprobe | CC0 | [tools/](https://github.com/codemyriad/cassini-format/blob/main/tools/cassini-extract.py) |
| `cassini-pack.py` | Packs Ogg Opus audio and timed words into a Cassini file | Python, stdlib only | CC0 | [tools/](https://github.com/codemyriad/cassini-format/blob/main/tools/cassini-pack.py) |
| `cassini-opus-digest.py` | Computes `exact-opus-audio-v1` from the spec alone | Python, stdlib only | CC0 | [tools/](https://github.com/codemyriad/cassini-format/blob/main/tools/cassini-opus-digest.py) |
| `cassini-read.js` | Reads a file in the browser: `fetch`, `DecompressionStream`, `crypto.subtle` | JavaScript, no dependencies | CC0 | [tools/](https://github.com/codemyriad/cassini-format/blob/main/tools/cassini-read.js) |
| Conformance suite | Test vectors and an adapter protocol for testing a reader in any language | Python harness | CC0 | [Run it](#check-a-file-then-test-your-implementation) |
| ffprobe one-liner | Dumps the payload with no script and no library | Shell | — | [The payload, in one pipeline](/consume/#the-payload-in-one-pipeline) |

The guides show them in use: [read a file in code](/consume/) and
[create a Cassini file](/produce/).

## Check a file, then test your implementation

Checking a file answers questions about that recording. A reader
also needs to behave correctly when metadata is absent, newer than it understands,
or damaged. The conformance suite exercises those cases and distinguishes required
behavior from advisory warnings.

For a first run you need **Git, Python 3 and Node.js 22 or newer**. The suite
and standalone JavaScript reader require no npm packages. In a fresh directory:

```bash
GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 https://github.com/codemyriad/cassini-format.git
cd cassini-format/spec/conformance
python3 run-conformance.py --adapter 'node adapters/adapter-js.mjs' --profile metadata
```

The small conformance fixtures are included in Git. Skipping LFS avoids downloading
the larger website demos, which this command does not use. The summary reports
passes, warnings, failures and skips. Read any warnings; a zero-failure run does
not mean every advisory behavior was implemented.

To test your own reader, write an adapter that accepts a file path and prints
one observation JSON object. The [suite README and worked adapters](https://github.com/codemyriad/cassini-format/tree/main/spec/conformance)
define those fields. Use `metadata` when your reader does not check audio, or
`full` when it does. Then replace the adapter command above with yours.

Record the repository revision you tested against. Re-run the suite when your
reader or the contract changes, and include your own representative files.

## Build with a coding assistant

The [complete specification as text](/llms-full.txt) includes the contracts,
implementation guides, schemas and sample file facts. Give it
to your assistant, then run the same file checks and conformance suite you would
use for any other implementation.

## Report an implementation

If you build one, say so: a format that only one program reads is not really a format.

[Open an issue](https://github.com/codemyriad/cassini-format/issues)
