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

## Meeting downloads

The shared viewer can copy or download the displayed transcript as Markdown
(`.md`) and download the original meeting audio file. This works for the
example recording and files opened locally in the browser.

## Where the content comes from

The home page is built around the three things a specification site has to
communicate: the spec and what changed in it, the tools for working with files,
and who implements it. Its example block puts the viewer, the tag dump, the
decoded manifest and the download link together, so a visitor can see that the
words on screen come from the tags in the file they can download. `/spec/` is the
reference hub for the versioned contracts and schemas, and `/changelog/` renders
`../CHANGELOG.md`. `/build/` is the tools hub: every reader and producer with its
language and licence, plus the conformance setup. `/try/` opens the example or
a local `.opus`/`.ogg` file in the shared transcript player; local files are
read directly in the browser. The player uses Cassini’s transcript component,
including inline interjections and word playback highlighting. Hover highlights
individual words; click one to seek to it. `/karaoke/` keeps the separate song
karaoke view, unlisted. `/consume/` and `/produce/` carry a visitor from sample
inputs to a useful result. Keep prerequisites and working directories explicit
when editing guides. The producer example downloads a matching `.words.json`
alongside the demo audio; update both fixtures together when changing the
example.

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

The standalone readers and producer are CC0. The transcript player is Cassini's
AGPL-3.0 viewer, loaded from `dist.gocassini.com` and not part of this
repository; see [the Cassini transcript component](#the-cassini-transcript-component).

## Deploying

`build/` is the whole site. Upload it. The pages are directory-shaped
(`/spec/index.html`), so the host needs to serve `index.html` for a directory
URL, which every static host does by default. `404.html` is the not-found page.

Production uses Cloudflare Pages Direct Upload, project `cassini-format`.
Every push to `main` deploys automatically through
`.github/workflows/site.yml`, which also builds every pull request. Before
building, it runs `npm run check` and `npm test`; a failure in
either stops the deploy. It needs
the repository secrets `CLOUDFLARE_API_TOKEN` (Cloudflare Pages: Edit on the
Code Myriad account) and `CLOUDFLARE_ACCOUNT_ID`.

To deploy by hand, build from a clean checkout of merged `main` (including Git
LFS demo assets), so unrelated local static files cannot enter the deployment:

```bash
npm ci
npm run check:embed
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

The players show recordings in Cassini's published viewer, the
`<cassini-meeting>` embed. The site loads it the way any page does, with one
script from `https://dist.gocassini.com/embed/<version>/viewer.js`. Its contract
is gocassini's
[`cassini-viewer/ATTRIBUTES.md`](https://github.com/codemyriad/gocassini/blob/main/cassini-viewer/ATTRIBUTES.md).
Turn reconstruction, inline interjections, overlap labels, word seeking,
playback and follow behavior are all Cassini's. The site has no transcript
renderer of its own and no copy of the viewer's source.

`src/lib/viewer/embed.ts` pins one exact viewer version. To move to a newer
viewer, change `CASSINI_EMBED_VERSION` there, then check the example and a
local file on `/try/`. `npm run check:embed`, which CI runs too, fails if the
pinned build lacks a feature `CassiniEmbed.svelte` uses. To try an unreleased viewer, build it in a gocassini
checkout with `npm run build:public -w cassini-viewer`, serve `dist/public/`,
and point the site at it:

```bash
VITE_CASSINI_EMBED_SRC=http://localhost:4178/embed/viewer.js npm run dev
```

`src/lib/viewer/CassiniEmbed.svelte` gives the element a blob URL of the bytes
the page has already read, so a local file never leaves the browser and the
example is not downloaded twice. It uses `layout="inline"`, because the page
around it shows the title and file details. It sets the embed's
`--cassini-color-*` properties from the site's palette, and follows the site's
light/dark switch through `theme`. The viewer draws inside its own shadow root,
so neither stylesheet reaches the other. It hides the "Recorded with Cassini"
badge, because a file opened on `/try/` may come from any producer.
