import type { ReadResult } from '../reader/cassini';
import { buildTranscriptIndex } from '../vendor/cassini-viewer/src/core/transcript';
import {
	buildTranscriptWordsFromPortable,
	buildReadableTranscriptFromPortable,
	buildDisplayTranscriptFromArtifacts,
	type PortableMeetingManifest
} from '../vendor/cassini-viewer/src/viewer/portable';
import type { DataProvider } from '../vendor/cassini-viewer/src/viewer/dataProvider';
import type { LoadedArtifact } from '../vendor/cassini-viewer/src/viewer/loadArtifact';

/** Feed verified reader output through Cassini's own portable display projection. */
export function toViewerArtifact(read: ReadResult, audioSrc: string): LoadedArtifact {
	if (!read.manifest || !read.transcript) throw new Error('No embedded transcript is available.');
	const portable: PortableMeetingManifest = {
		...read.manifest,
		transcript: { items: read.transcript.words }
	};
	const transcript = buildTranscriptWordsFromPortable(portable, audioSrc);
	const readableTranscript = buildReadableTranscriptFromPortable(portable, transcript);
	const displayTranscript = buildDisplayTranscriptFromArtifacts(transcript, readableTranscript);
	const timing = read.manifest.provenance?.wordTimings;
	const wordEndsBoundedByAudio =
		!!timing &&
		typeof timing === 'object' &&
		'endsBoundedByAudio' in timing &&
		timing.endsBoundedByAudio === true;
	return {
		transcript,
		readableTranscript,
		displayTranscript,
		index: buildTranscriptIndex(transcript),
		audioSrc,
		summary: null,
		captionsSrc: null,
		chaptersSrc: null,
		metadata: null,
		timingPrecision: {
			level: 'word',
			label: 'Word-timed',
			detail: 'Word timings supplied by the file.'
		},
		wordEndsBoundedByAudio,
		availableTranscripts: [
			{ id: read.transcript.entry.id, label: 'Transcript', description: '', isDefault: true }
		],
		currentTranscriptId: read.transcript.entry.id
	};
}

/** The adapter supplies already-read bytes; the viewer never uploads a local file. */
export function singleArtifactProvider(artifact: LoadedArtifact): DataProvider {
	return {
		loadCatalog: async () => null,
		loadMeetingForEntry: async () => artifact,
		loadMeetingSummary: async () => null,
		switchTranscript: async () => artifact,
		loadBundledArtifact: async () => artifact
	};
}
