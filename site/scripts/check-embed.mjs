#!/usr/bin/env node
// Check that the pinned Cassini embed can do what this site asks of it.
//
//   node scripts/check-embed.mjs            # the version pinned in embed.ts
//   node scripts/check-embed.mjs <url>      # any viewer.js, e.g. a local build
//
// CassiniEmbed.svelte relies on features of the embed contract that only some
// published versions have. A pin to a version without them still loads, but
// renders the wrong layout, ignores the site's palette and theme, and never
// reports playback errors. This fails the build instead. Each feature below
// leaves a string in the minified bundle that no older build contains.

import { readFileSync } from 'node:fs';

const REQUIRED = [
	['layout="inline"', 'data-layout="inline"'],
	['--cassini-color-* palette', '--cassini-color-base-100'],
	['--cassini-font-sans', '--cassini-font-sans'],
	['live theme attribute', 'observedAttributes'],
	['playbackerror event', 'playbackerror']
];

const pinned = readFileSync(new URL('../src/lib/viewer/embed.ts', import.meta.url), 'utf8');
const version = /CASSINI_EMBED_VERSION = '([^']+)'/.exec(pinned)?.[1];
const src = process.argv[2] ?? `https://dist.gocassini.com/embed/${version}/viewer.js`;

const fetchText = async (url) => {
	const response = await fetch(url);
	if (!response.ok) throw new Error(`${url}: ${response.status}`);
	return response.text();
};

const script = await fetchText(src);
await fetchText(new URL('viewer.css', src));
const missing = REQUIRED.filter(([, marker]) => !script.includes(marker)).map(([feature]) => feature);
if (missing.length) {
	console.error(`check-embed: ${src} lacks what CassiniEmbed.svelte uses: ${missing.join(', ')}.`);
	console.error('check-embed: pin a newer version in src/lib/viewer/embed.ts.');
	process.exit(1);
}
console.log(`check-embed: ${src} has every feature this site uses.`);
