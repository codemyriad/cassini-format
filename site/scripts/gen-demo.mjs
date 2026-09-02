/**
 * Reads the published demo .opus and writes the facts the site quotes.
 *
 * The point: every tag name, byte count and word timing shown on the site comes
 * out of the file a visitor can download, not out of a copy someone typed. Run
 * it again whenever the demo file changes.
 *
 *   node scripts/gen-demo.mjs [path/to/demo.opus]
 */
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { readFile, writeFile, mkdir, stat } from 'node:fs/promises';
import { gunzipSync } from 'node:zlib';
import { createHash } from 'node:crypto';
import path from 'node:path';

const run = promisify(execFile);
const HERE = path.dirname(new URL(import.meta.url).pathname);
const SITE = path.resolve(HERE, '..');

const candidates = [
	process.argv[2],
	path.join(SITE, 'static/demo/lantern-festival.opus')
].filter(Boolean);

let file;
for (const c of candidates) {
	try {
		await stat(c);
		file = c;
		break;
	} catch {
		/* try the next one */
	}
}
if (!file) {
	console.error('No demo file found. Tried:\n' + candidates.map((c) => '  ' + c).join('\n'));
	process.exit(1);
}

const { stdout } = await run('ffprobe', [
	'-v',
	'error',
	'-show_entries',
	'stream_tags:format=duration,size,bit_rate',
	'-show_entries',
	'stream=codec_name,sample_rate,channels',
	'-of',
	'json',
	file
]);
const probe = JSON.parse(stdout);
const tags = {};
for (const s of probe.streams ?? []) Object.assign(tags, s.tags ?? {});
Object.assign(tags, probe.format?.tags ?? {});

const isChunk = (k) => /_PAYLOAD_\d{3}$/.test(k);
const b64urlToBuf = (s) => Buffer.from(s.replace(/-/g, '+').replace(/_/g, '/'), 'base64');

function decodeChunkSet(prefix, count) {
	let blob = '';
	for (let i = 0; i < count; i++) {
		const v = tags[`${prefix}${String(i).padStart(3, '0')}`];
		if (v === undefined) throw new Error(`missing chunk ${prefix}${String(i).padStart(3, '0')}`);
		blob += v;
	}
	const raw = gunzipSync(b64urlToBuf(blob));
	return { json: JSON.parse(raw.toString('utf8')), sha256: createHash('sha256').update(raw).digest('hex'), rawBytes: raw.length };
}

const manifest = decodeChunkSet('CASSINI_PAYLOAD_', Number(tags.CASSINI_PAYLOAD_CHUNK_COUNT));

const defaultId = tags.CASSINI_TRANSCRIPT_DEFAULT;
const entry = (manifest.json.transcripts ?? []).find((t) => t.id === defaultId) ?? manifest.json.transcripts?.[0];
const body = entry
	? decodeChunkSet(entry.payloadRef.prefix, entry.payloadRef.chunkCount)
	: null;

const bytes = (await readFile(file)).length;
const words = body?.json?.items ?? [];
const speakers = Object.fromEntries((manifest.json.speakers ?? []).map((s) => [s.id, s.label]));

// A turn is a maximal run of consecutive items with the same speaker. No gap
// heuristic: items are in speaker-turn order, not time order, and splitting on
// a timestamp gap would break a turn wherever somebody paused.
const turns = [];
for (const w of words) {
	const last = turns.at(-1);
	if (last && last.speaker === w.speaker) {
		last.words.push(w);
		last.endMs = Math.max(last.endMs, w.endMs);
	} else {
		turns.push({ speaker: w.speaker, label: speakers[w.speaker] ?? w.speaker, startMs: w.startMs, endMs: w.endMs, words: [w] });
	}
}

const out = {
	generatedFrom: path.basename(file),
	bytes,
	audio: probe.streams?.[0]
		? {
				codec: probe.streams[0].codec_name,
				sampleRate: Number(probe.streams[0].sample_rate),
				channels: probe.streams[0].channels
			}
		: null,
	tagNames: Object.keys(tags).sort(),
	commentCount: Object.keys(tags).length,
	chunkTagCount: Object.keys(tags).filter(isChunk).length,
	// Everything a human reads, with the base64 walls left out.
	readableTags: Object.fromEntries(
		Object.entries(tags)
			.filter(([k]) => !isChunk(k))
			.sort(([a], [b]) => a.localeCompare(b))
	),
	sampleChunkTag: (() => {
		const k = Object.keys(tags).filter(isChunk).sort()[0];
		return k ? { key: k, value: tags[k] } : null;
	})(),
	manifest: manifest.json,
	manifestBytes: manifest.rawBytes,
	manifestSha256: manifest.sha256,
	transcript: entry
		? {
				id: entry.id,
				role: entry.role,
				format: entry.format,
				wordCount: words.length,
				rawBytes: body.rawBytes,
				gzipBytes: Number(tags[`${entry.payloadRef.prefix}GZIP_BYTES`] ?? 0),
				chunkCount: entry.payloadRef.chunkCount
			}
		: null,
	speakers,
	turns: turns.map((t) => ({ ...t, text: t.words.map((w) => w.text).join(' ') })),
	firstWords: words.slice(0, 12)
};

await mkdir(path.join(SITE, 'src/lib/generated'), { recursive: true });
await writeFile(path.join(SITE, 'src/lib/generated/demo.json'), JSON.stringify(out, null, '\t') + '\n');

const tagBytes = out.readableTags && Object.entries(tags).reduce((n, [k, v]) => n + k.length + v.length + 5, 0);
console.log(
	`demo.json written from ${path.basename(file)}\n` +
		`  ${bytes.toLocaleString()} B file, ${out.commentCount} comments (${out.chunkTagCount} chunk tags), ~${tagBytes.toLocaleString()} B of tags\n` +
		`  manifest ${out.manifestBytes} B raw, transcript ${out.transcript?.wordCount} words in ${out.transcript?.chunkCount} chunks\n` +
		`  ${out.turns.length} turns, ${Object.keys(out.speakers).length} speakers`
);
