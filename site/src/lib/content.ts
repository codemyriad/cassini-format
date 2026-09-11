import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { renderMarkdown } from '$lib/markdown';
import demo from '$lib/generated/demo.json';

/**
 * Output pasted into prose goes stale the moment the demo file changes, and a
 * site whose whole claim is "this was run against a real file" cannot afford
 * that. So the blocks that quote the demo are substituted at build time from
 * the same generated facts every other page uses.
 *
 * It has already caught one: swapping the demo file left three timestamps in
 * the reading guide describing a recording that no longer existed.
 */
const substitutions: Record<string, () => string> = {
	'demo.turns': () =>
		demo.turns
			.slice(0, 3)
			.map((t) => `[${t.startMs / 1000}s] ${t.speaker}: ${t.text}`)
			.join('\n'),
	'demo.filename': () => demo.generatedFrom,
	'demo.wordInput': () => demo.generatedFrom.replace(/\.(opus|ogg)$/, '.words.json'),
	'demo.sampleCount': () => String(demo.readableTags.CASSINI_AUDIO_SAMPLE_COUNT),
	'demo.sampleRate': () => String(demo.audio.sampleRate),
	'demo.durationMs': () => String(demo.readableTags.CASSINI_AUDIO_DURATION_MS),
	'demo.title': () => String(demo.readableTags.TITLE ?? ''),
	'demo.transcriptId': () => String(demo.transcript?.id ?? ''),
	'demo.transcriptPrefix': () =>
		String(demo.manifest.transcripts.find((entry) => entry.id === demo.transcript?.id)?.payloadRef.prefix ?? ''),
	'demo.words': () => String(demo.transcript?.wordCount ?? 0),
	'demo.speakers': () => String(Object.keys(demo.speakers).length),
	'demo.comments': () => String(demo.commentCount),
	'demo.bytes': () => demo.bytes.toLocaleString(),
	'demo.audioDigest': () => String(demo.readableTags.CASSINI_AUDIO_OPUS_SHA256 ?? '')
};

function substitute(markdown: string, source: string): string {
	return markdown.replace(/\{\{([a-zA-Z.]+)\}\}/g, (whole, key: string) => {
		const fn = substitutions[key];
		if (!fn) throw new Error(`${source}: unknown substitution {{${key}}}`);
		return fn();
	});
}

/** Prose authored for the site itself, as opposed to documents lifted from the repo. */
export async function loadContent(name: string) {
	const source = `site/src/content/${name}.md`;
	const raw = await readFile(path.resolve('src/content', `${name}.md`), 'utf8');
	return renderMarkdown(substitute(raw, source), source);
}

export const contentSource = async (name: string) =>
	substitute(
		await readFile(path.resolve('src/content', `${name}.md`), 'utf8'),
		`site/src/content/${name}.md`
	);
