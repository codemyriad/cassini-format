# Cassini's transcript component

This directory vendors the exported `MeetingView.svelte` and its supporting
transcript model from [codemyriad/gocassini](https://github.com/codemyriad/gocassini),
pinned to commit
[`297d57b6b2520829072ea8d270eb8e7e693e3599`](https://github.com/codemyriad/gocassini/tree/297d57b6b2520829072ea8d270eb8e7e693e3599/cassini-viewer).
It is licensed under **AGPL-3.0**, with the complete upstream license retained in
[LICENSE](LICENSE). It is an explicit exception to the format repository's CC0
reference-code license.

The site uses the actual Cassini component, including D-693's inline
interjections and reconstructed speaker turns, D-690's acoustic overlap
judgments, and D-692's playback index. There is no separate implementation of
these behaviors in the format-site player.

[`upstream.json`](upstream.json) records upstream file paths, the source commit,
original hashes, and hashes of the two files with integration patches. The
repeatable patches live in [`scripts/sync-viewer.mjs`](../../../../scripts/sync-viewer.mjs):

- `MeetingView.svelte`: opt-in scrolling and Space shortcuts confined to the
  embedded panel; media failures reported to the host player; the embedded
  transcript does not introduce a second main landmark inside the page.
- `viewer/portable.ts`: optional-value narrowing and type assertions required by
  the site's TypeScript checker. The projection's runtime behavior is unchanged.

The remaining source files, including all overlap and interjection logic, are
verbatim upstream source. Upstream core tests are retained and run by
`npm run test:viewer`. The host's data adapter and shadow-DOM wrapper live in
[`src/lib/viewer`](../../viewer/); theme and card sizing are adapted there.

Upstream commit `85ebf1a` (D-654) unintentionally removed word interactions.
[D-734](https://linear.app/code-myriad/issue/D-734/restore-word-level-transcript-highlighting-and-seeking-in-the-cassini)
restores word hover, seeking and playback highlighting in the shared component.
This site consumes that implementation from the pinned revision. Word rendering,
timing lookup and highlighting styles come from Cassini, with no site-specific
word mode or duplicate implementation. The host stylesheet supplies the site's
theme colors and card sizing.

Run `npm run check:viewer` to verify the pinned snapshot. To update it, run:

```bash
node scripts/sync-viewer.mjs --from /path/to/gocassini --ref COMMIT
npm run gen:viewer-css
npm run test:viewer
npm run check
npm run build
```

The sync script reads Git objects without switching or changing the upstream
checkout. Exact patch matches make an incompatible upstream update fail for
review instead of silently changing the renderer.
