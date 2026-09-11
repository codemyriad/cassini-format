# The format website

The public site for the Cassini portable meeting format at
<https://format.gocassini.com/>. SvelteKit with
`adapter-static`, so `npm run build` produces a plain directory of files that any
static host will serve. There is no server side and nothing host-specific in the
config.

```bash
npm ci
npm run dev          # http://localhost:5173
npm run build        # -> build/
npm run preview      # serve build/ locally
```

## Where the content comes from

The homepage introduces the format through our Nextcloud Talk use case: use the
transcript to find a passage, then listen to check what was actually said. The
playable example and creation/sharing/reading workflow keep that purpose visible.
`/using/` explains fit,
compatibility and limitations; `/build/` connects the implementation guides to
file checks and conformance tests. `/try/` opens the example or
a local `.opus`/`.ogg` file in the shared transcript player; local files are
read directly in the browser. The player uses Cassini’s transcript component,
including inline interjections and word playback highlighting. Hover highlights
individual words; click one to seek to it. `/demo/` keeps the separate song karaoke view. `/spec/` is the
reference hub for the versioned contracts, schemas and conformance suite.
`/consume/` and `/produce/` carry a visitor from sample inputs to a useful result;
`/verify/` provides the shared checking workflow and explains the scope of each
result. Keep prerequisites and working directories explicit when editing guides.
The producer example downloads a matching `.words.json` alongside the demo audio;
update both fixtures together when changing the example.

Most of the site is not written here. The specification pages render
`../SPEC.md` and `../spec/*.md` directly, and the design notes render
`../design/*.md`, so those files stay the source of truth and stay readable on
GitHub. Only the guides (`src/content/*.md`) are written for the site.

`src/lib/markdown.ts` is the pipeline: remark to rehype, Shiki for highlighting,
plus a link rewriter that turns the repository's relative markdown links into
site routes.

Two prerender settings in `vite.config.ts` do more work than they look like:

```ts
prerender: { handleHttpError: 'fail', handleMissingId: 'fail' }
```

Together they make the build a link and anchor checker for the specification. A
dead cross-reference in `SPEC.md`, or a `#heading` that no longer exists, fails
the build instead of shipping.

## The demo file

`static/demo/cassini-final-moments.opus` is a valid `org.cassini.portable-meeting/1`
file containing NASA/JPL’s “Final Moments in Cassini Mission Control.” Courtesy
NASA/JPL-Caltech. The full stereo audio includes a reconciled transcript from
Gemini 3.5 Flash, Gemini 3.8 Flash, OpenAI GPT Audio, Scribe v2 and JPL captions.
Scribe supplies acoustic word timings. Named speakers are sourced to JPL;
unresolved voices and speech remain explicitly uncertain. Source credit and
production provenance are embedded in the file.

The earlier repair café recordings and source tracks remain available; their
production notes are in `static/demo/repair-cafe.README.md`. The site’s current
file facts come from the NASA/JPL example:

```bash
node scripts/gen-demo.mjs          # -> src/lib/generated/demo.json
```

That script runs `ffprobe`, decodes the manifest and the transcript body, and
writes the tag list, byte counts, speaker table and turns that the pages quote.
Re-run it whenever the demo file changes; the numbers on the site update with it.
It is the only build step that needs `ffprobe`, and its output is committed, so a
plain `npm run build` does not.

See `static/demo/README.md` for the script and how the audio was made.

The standalone readers and producer are CC0. The transcript interface is
Cassini’s AGPL-3.0 component; its vendored source and license are included in
`src/lib/vendor/cassini-viewer/`.

## Deploying

`build/` is the whole site. Upload it. The pages are directory-shaped
(`/spec/index.html`), so the host needs to serve `index.html` for a directory
URL, which every static host does by default. `404.html` is the not-found page.

Production uses Cloudflare Pages Direct Upload, project `cassini-format`.
Build from a clean checkout of merged `main` (including Git LFS demo assets),
so unrelated local static files cannot enter the deployment:

```bash
npm ci
SITE_URL=https://format.gocassini.com npm run build
wrangler pages deploy build --project-name cassini-format --branch main
```

Canonical links and the URLs in `llms.txt` and `llms-full.txt` default to
`https://format.gocassini.com`. `SITE_URL` overrides the complete site root;
set it to an empty string for relative links in a portable preview. Wrangler
needs the configured Cloudflare credentials and account. After deployment,
verify `https://format.gocassini.com/`, `/schema/`, and `/llms-full.txt`.

Schema `$id` values and new recordings’ `CASSINI_PAYLOAD_SCHEMA` tags use
`https://format.gocassini.com/schema/`.

For a deploy under a subpath rather than a domain root, set `BASE_PATH`:

```bash
BASE_PATH=/cassini-format npm run build
```

## The Cassini transcript component

The players mount Cassini's actual exported `MeetingView.svelte`, including its
turn reconstruction, inline interjections, overlap labels, playback and follow
behavior. This is a pinned source dependency, not a second transcript renderer.
`src/lib/vendor/cassini-viewer/upstream.json` records the upstream commit and
SHA-256 of every source file. The vendored component and model are **AGPL-3.0**;
their upstream license is retained in that directory. This exception does not
change the CC0 license of `src/lib/reader/cassini.ts` or the standalone readers.

`src/lib/viewer/artifact.ts` adapts the format reader's verified manifest and
words through Cassini's own portable projection. `CassiniView.svelte` mounts the
component in a shadow root so its own stylesheet cannot affect the surrounding
site; `embedding.css` only adapts the card layout and theme. Local files remain
in browser memory and use a blob URL for playback.

Word hover, seeking and playback highlighting come from Cassini's shared
component, restored under [D-734](https://linear.app/code-myriad/issue/D-734/restore-word-level-transcript-highlighting-and-seeking-in-the-cassini).
The site does not maintain a separate word renderer or playback index.
The reproducible patch in `scripts/sync-viewer.mjs` adds only embedding fixes
(scoped Space shortcuts, scrolling within the panel, playback errors) and
TypeScript narrowing. Cassini owns word interactions, transcript wording,
turn reconstruction and interjection placement. To update from a Cassini checkout:

```bash
node scripts/sync-viewer.mjs --from /path/to/gocassini --ref COMMIT
npm run gen:viewer-css
npm run test:viewer
npm run check
npm run build
```

`npm run build` checks the pinned source hashes and regenerates the component
stylesheet. `npm run test:viewer` runs the upstream timing, overlap, playhead and
transcript regression suites plus the format adapter and word playback tests. The
upstream test files are excluded from the site's TypeScript diagnostics and run
with their native Vitest runner.
