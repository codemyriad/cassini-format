/**
 * The site's browser reader (src/lib/reader/cassini.ts) is also published as a
 * standalone example at ../tools/cassini-read.js. Generating one from the other
 * is the only way the page can honestly say it runs the file you can download.
 *
 *   node scripts/gen-reader.mjs           # write ../tools/cassini-read.js
 *   node scripts/gen-reader.mjs --check   # fail if it is out of date
 */
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { readFile, writeFile, mkdtemp } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';

const run = promisify(execFile);
const SITE = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const SOURCE = path.join(SITE, 'src/lib/reader/cassini.ts');
const TARGET = path.join(SITE, '../tools/cassini-read.js');

const out = await mkdtemp(path.join(tmpdir(), 'cassini-reader-'));
await run('npx', [
	'tsc',
	'--ignoreConfig',
	SOURCE,
	'--target', 'es2022',
	'--module', 'esnext',
	'--moduleResolution', 'bundler',
	'--lib', 'es2022,dom',
	'--removeComments', 'false',
	'--outDir', out
]);

const generated = await readFile(path.join(out, 'cassini.js'), 'utf8');

if (process.argv.includes('--check')) {
	const current = await readFile(TARGET, 'utf8').catch(() => '');
	if (current !== generated) {
		console.error(
			`${path.relative(process.cwd(), TARGET)} is out of date with ${path.relative(process.cwd(), SOURCE)}.\n` +
				'Run: npm run gen:reader'
		);
		process.exit(1);
	}
	console.log('tools/cassini-read.js is in sync with the site reader');
} else {
	await writeFile(TARGET, generated);
	console.log(`wrote ${path.relative(process.cwd(), TARGET)} (${generated.length} bytes)`);
}
