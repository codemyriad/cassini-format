import { describe, expect, it } from 'vitest';
import { readFile } from 'node:fs/promises';
import { readCassini, type ReadResult, type Word } from '../reader/cassini';
import { toViewerArtifact, singleArtifactProvider } from './artifact';
import { judgedDisplaySegments } from '../vendor/cassini-viewer/src/core/transcript';
import { buildTranscriptRows } from '../vendor/cassini-viewer/src/core/overlap';

function fixture(): ReadResult {
	const words: Word[] = 'We can move the queue inside and keep the doorway clear.'
		.split(' ')
		.map((text, index) => ({
			text,
			speaker: 'maya',
			startMs: index * 400,
			endMs: index * 400 + 350
		}));
	words.push({ text: 'Right.', speaker: 'jonah', startMs: 1700, endMs: 2100 });
	words.sort((a, b) => a.startMs - b.startMs);
	return {
		state: 'unverified',
		classification: 'cassini',
		cassini: true,
		tags: new Map(),
		verified: { manifest: true, transcript: true },
		warnings: [],
		manifest: {
			kind: 'cassini-portable-meeting',
			version: 1,
			profile: 'embedded',
			meeting: { title: 'The rain plan', durationMs: 5000 },
			audio: {},
			integrity: {},
			speakers: [
				{ id: 'maya', label: 'Maya' },
				{ id: 'jonah', label: 'Jonah' }
			],
			provenance: { wordTimings: { endsBoundedByAudio: true } }
		},
		transcript: {
			entry: {
				id: 'words',
				format: 'word',
				payloadRef: { prefix: 'WORDS', chunkCount: 1, sha256: '' }
			},
			words
		}
	};
}

describe('the format reader → Cassini viewer boundary', () => {
	it('reconstructs an overlapping backchannel inline without losing or retiming words', () => {
		const read = fixture();
		const original = structuredClone(read.transcript!.words);
		const artifact = toViewerArtifact(read, 'blob:local');
		const rows = buildTranscriptRows(
			judgedDisplaySegments(artifact.index, artifact.displayTranscript!)
		);
		expect(rows).toHaveLength(1);
		expect(rows[0].speakerLabel).toBe('Maya');
		const chip = rows[0].members.find((member) => member.kind === 'interjection');
		expect(chip?.kind).toBe('interjection');
		if (chip?.kind === 'interjection') {
			expect(chip.speakerLabel).toBe('Jonah');
			expect(chip.blocks.map((block) => block.text).join(' ')).toBe('Right.');
			expect(chip.blocks[0].startMs).toBe(1700);
		}
		expect(
			artifact.transcript.segments.map((segment) => ({
				text: segment.text,
				speaker: segment.speaker,
				startMs: segment.startMs,
				endMs: segment.endMs
			}))
		).toEqual(original);
		expect(read.transcript!.words).toEqual(original);
		expect(artifact.wordEndsBoundedByAudio).toBe(true);
	});

	it('keeps uncertain attribution available to the actual Cassini renderer', () => {
		const read = fixture();
		read.transcript!.words[0].lowConfidenceSpeaker = true;
		read.transcript!.words[0].attributionGapDb = 19;
		const word = toViewerArtifact(read, 'blob:local').index.segments[0].words[0];
		expect(word.lowConfidenceSpeaker).toBe(true);
		expect(word.attributionGapDb).toBe(19);
	});

	it('serves a local artifact without fetching or uploading anything', async () => {
		const artifact = toViewerArtifact(fixture(), 'blob:local');
		const provider = singleArtifactProvider(artifact);
		expect(await provider.loadBundledArtifact()).toBe(artifact);
		expect(await provider.loadCatalog()).toBeNull();
	});

	it('retains the ordinary-audio fallback when there is no readable transcript', async () => {
		const bytes = await readFile('../spec/conformance/opus/002-plain-audio.opus');
		const read = await readCassini(
			bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength)
		);
		expect(read.state).toBe('plain-audio');
		expect(() => toViewerArtifact(read, 'blob:local')).toThrow('No embedded transcript');
	});

	it('renders all four real overlaps in the published repair café fixture as inline interjections', async () => {
		const bytes = await readFile('static/demo/repair-cafe.opus');
		const read = await readCassini(
			bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength)
		);
		const artifact = toViewerArtifact(read, 'blob:demo');
		const rows = buildTranscriptRows(
			judgedDisplaySegments(artifact.index, artifact.displayTranscript!)
		);
		const chips = rows.flatMap((row) =>
			row.members.filter((member) => member.kind === 'interjection')
		);
		expect(chips).toHaveLength(4);
		expect(artifact.transcript.segments).toHaveLength(read.transcript!.words.length);
		expect(read.verified).toEqual({ manifest: true, transcript: true });
	});
});
