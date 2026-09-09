import demo from '$lib/generated/demo.json';
import { highlight } from '$lib/markdown';

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

export async function load() {
	const manifest = demo.manifest;

	return {
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
		manifestHtml: await highlight(JSON.stringify(manifest, null, 2), 'json'),
		wordHtml: await highlight(JSON.stringify(demo.firstWords[0], null, 2), 'json')
	};
}
