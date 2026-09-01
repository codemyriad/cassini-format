# The format website

The public site for the Cassini portable meeting format. SvelteKit with
`adapter-static`, so `npm run build` produces a plain directory of files that any
static host will serve. There is no server side and nothing host-specific in the
config.

```bash
npm install
npm run dev          # http://localhost:5173
npm run build        # -> build/
npm run preview      # serve build/ locally
```

## Where the content comes from

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

`static/demo/lantern-festival.opus` is a real
`org.cassini.portable-meeting/1` file. Everything the site says about it comes
out of the file itself:

```bash
node scripts/gen-demo.mjs          # -> src/lib/generated/demo.json
```

That script runs `ffprobe`, decodes the manifest and the transcript body, and
writes the tag list, byte counts, speaker table and turns that the pages quote.
Re-run it whenever the demo file changes; the numbers on the site update with it.
It is the only build step that needs `ffprobe`, and its output is committed, so a
plain `npm run build` does not.

See `static/demo/README.md` for how the file itself was made.

## Deploying

`build/` is the whole site. Upload it. The pages are directory-shaped
(`/spec/v3/index.html`), so the host needs to serve `index.html` for a directory
URL, which every static host does by default. `404.html` is the not-found page.

For a deploy under a subpath rather than a domain root, set `BASE_PATH`:

```bash
BASE_PATH=/cassini-format npm run build
```
