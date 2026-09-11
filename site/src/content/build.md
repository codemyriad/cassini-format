The format is the contract between applications. You can reuse a standalone
reader or producer, or implement that contract yourself. Start with the outcome
you need; each guide explains its inputs, gives a working path, and connects to
the checks that tell you what you have built.

To explore a recording without code, [open the browser player](/try/).
If you are deciding whether the format fits, start with [Using Cassini](/using/).

## Choose what you want to build

| Your goal | Start here | What you will have |
| --- | --- | --- |
| Use a recording's transcript in your application | [Read a file in code](/consume/) | Words, timestamps and speaker data in Python or JavaScript, with the reader's reported state. |
| Export recordings from your application | [Create a Cassini file](/produce/) | One `.opus` file containing your existing audio and timed words, with the audio packets preserved. |
| Establish that a file is ready to share | [Check a file](/verify/) | Separate checks for readable metadata, audio matching, and JSON structure, with the limits of each result. |
| Write an independent implementation | [Specification & schemas](/spec/) | The normative contracts, plus the conformance workflow below to test reader behavior. |

## Know which pieces you are reusing

The standalone Python reader, Python producer and JavaScript reader are CC0.
They use standard-library or browser APIs. Their guides list any additional
tools needed for optional inspection and validation steps.

The transcript interface displayed on this site is a separate component from
the gocassini application, licensed under AGPL-3.0. You can use the CC0 reader
to obtain data and build an interface of your own. The format does not require
the particular viewer shown in the demo.

Use the **guides** to get from inputs to a result. Use the **specification** to
settle required behavior and edge cases. Use the **design notes** to understand
why the contract took its present shape. The [project status](/status/) explains
which revisions existing implementations support.

## Check a file, then test your implementation

[Checking a file](/verify/) answers questions about that recording. A reader
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
implementation and verification guides, schemas and sample file facts. Give it
to your assistant, then run the same file checks and conformance suite you would
use for any other implementation.
