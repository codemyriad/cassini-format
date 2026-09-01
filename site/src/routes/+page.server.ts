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

const DECODE = `ffprobe -v error -show_entries stream_tags -of json meeting.opus \\
| jq -r '[.streams[0].tags | to_entries[]
          | select(.key | test("^CASSINI_PAYLOAD_[0-9]{3}$"))]
         | sort_by(.key) | map(.value) | join("")' \\
| awk '{ p=(4-length($0)%4)%4; printf "%s",$0; for(i=0;i<p;i++) printf "=" }' \\
| basenc --base64url -d | gunzip | jq .`;

/**
 * The real manifest is 1.5 KB and would dwarf everything else on the page.
 * Abridge it the way you would read it aloud: every top-level member present,
 * the repetitive arrays cut short and marked.
 */
function abridge() {
	const m = demo.manifest as Record<string, any>;
	const speakers = (m.speakers ?? []).slice(0, 2);
	const tx = (m.transcripts ?? [])[0];
	return {
		kind: m.kind,
		version: m.version,
		profile: m.profile,
		meeting: {
			id: m.meeting?.id,
			title: m.meeting?.title,
			recordedAtLocal: m.meeting?.recordedAtLocal,
			durationMs: m.meeting?.durationMs
		},
		audio: m.audio,
		integrity: { matchPolicy: m.integrity?.matchPolicy, opusAudioSha256: m.integrity?.opusAudioSha256 },
		speakers: [...speakers, `… ${(m.speakers ?? []).length - speakers.length} more`],
		transcripts: tx
			? [
					{
						id: tx.id,
						role: tx.role,
						default: tx.default,
						format: tx.format,
						payloadRef: {
							prefix: tx.payloadRef?.prefix,
							chunkCount: tx.payloadRef?.chunkCount,
							sha256: tx.payloadRef?.sha256
						}
					}
				]
			: [],
		// One provenance field is a paragraph explaining which timings are measured
		// and which are interpolated. Honest, but it would double this block.
		provenance: {
			speechToText: Object.fromEntries(
				Object.entries(m.provenance?.speechToText ?? {}).map(([id, step]: [string, any]) => [
					id,
					{ ...step, source: step?.source ? '…' : undefined }
				])
			)
		}
	};
}

export async function load() {
	const manifest = abridge();

	return {
		rows: rows(),
		demo: {
			bytes: demo.bytes,
			commentCount: demo.commentCount,
			words: demo.transcript?.wordCount ?? 0,
			speakers: Object.keys(demo.speakers).length,
			durationMs: Number(demo.readableTags.CASSINI_AUDIO_DURATION_MS ?? 0),
			gzipBytes: (demo.transcript?.gzipBytes ?? 0) + Number(demo.readableTags.CASSINI_PAYLOAD_GZIP_BYTES ?? 0),
			title: demo.readableTags.TITLE
		},
		decodeHtml: await highlight(DECODE, 'bash'),
		manifestHtml: await highlight(JSON.stringify(manifest, null, 2), 'json'),
		wordsHtml: await highlight(
			JSON.stringify(
				{ format: 'cassini.words.v1', items: demo.firstWords.slice(0, 4) },
				null,
				2
			),
			'json'
		)
	};
}
