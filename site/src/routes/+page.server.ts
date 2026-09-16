import demo from '$lib/generated/demo.json';
import { highlight } from '$lib/markdown';
import { readRepoFile } from '$lib/docs';

const STD = new Set(['TITLE', 'DATE', 'comment', 'encoder', 'DESCRIPTION', 'LANGUAGE']);
const DESC = new Set(['CASSINI_FORMAT', 'CASSINI_DECODE_HINT', 'CASSINI_PAYLOAD_ENCODING']);

/** The order ffprobe prints them in: ASCII, because that is how the producer sorts. */
function rows() {
	const all: { key: string; value: string; kind: 'std' | 'desc' | 'chunk' | 'sum' }[] = [];
	for (const [key, value] of Object.entries(demo.readableTags)) {
		all.push({
			key,
			value,
			kind: DESC.has(key) ? 'desc' : STD.has(key) ? 'std' : 'sum'
		});
	}
	// Slot one real chunk tag in where it belongs alphabetically, so the shape of
	// the thing is honest: the payload really is sitting in the comment header.
	if (demo.sampleChunkTag) {
		all.push({
			key: demo.sampleChunkTag.key,
			value: demo.sampleChunkTag.value.slice(0, 44) + '…',
			kind: 'chunk'
		});
	}
	return all.sort((a, b) => (a.key < b.key ? -1 : a.key > b.key ? 1 : 0));
}

/**
 * The most recent dated entry in CHANGELOG.md, for the hero pill and the spec
 * section. It is the first `### YYYY-MM-DD` heading under "Specification
 * changes", so adding an entry moves the date on the home page with it.
 */
async function latestChange() {
	const raw = await readRepoFile('CHANGELOG.md');
	const from = raw.indexOf('## Specification changes');
	const m = /^###\s+(\d{4}-\d{2}-\d{2})(?:\s*[—-]\s*(.+))?$/m.exec(
		from === -1 ? raw : raw.slice(from)
	);
	if (!m) throw new Error('CHANGELOG.md: no dated "### YYYY-MM-DD" entry to date the home page');
	return { date: m[1], title: (m[2] ?? '').trim() };
}

export async function load() {
	const manifest = demo.manifest;

	return {
		change: await latestChange(),
		rows: rows(),
		demo: {
			filename: demo.generatedFrom,
			bytes: demo.bytes,
			commentCount: demo.commentCount,
			words: demo.transcript?.wordCount ?? 0,
			speakers: Object.keys(demo.speakers).length,
			durationMs: Number(demo.readableTags.CASSINI_AUDIO_DURATION_MS ?? 0),
			gzipBytes:
				(demo.transcript?.gzipBytes ?? 0) +
				Number(demo.readableTags.CASSINI_PAYLOAD_GZIP_BYTES ?? 0),
			title: demo.readableTags.TITLE
		},
		manifestHtml: await highlight(JSON.stringify(manifest, null, 2), 'json')
	};
}
