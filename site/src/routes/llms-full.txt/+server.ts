import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { site } from '$lib/site';
import { origin } from '$lib/origin';
import { REPO } from '$lib/markdown';
import { listSchemas, readRepoFile } from '$lib/docs';
import { contentSource } from '$lib/content';
import demo from '$lib/generated/demo.json';

export const prerender = true;
export const trailingSlash = 'never';

const rule = (title: string) => `\n\n${'='.repeat(78)}\n${title}\n${'='.repeat(78)}\n\n`;

const siteContent = contentSource;

/**
 * The whole specification as one document, for handing to a model in one paste.
 */
export async function GET() {
	const parts: string[] = [];

	parts.push(`${site.formatName} format — the complete specification, flattened

This document: ${origin}/llms-full.txt
Wire version: ${site.formatId}
Spec text CC BY 4.0. Schemas, test vectors and standalone readers/producer CC0.
The site's embedded Cassini transcript component is AGPL-3.0.

WHAT THIS IS

Everything needed to write a reader or a producer, in one file: the
specification, the transcript body format, the audio digest contract,
implementation and verification guides, every JSON Schema, and the actual tag dump of a real file
you can download and check against.

HOW TO USE IT

The specification is the rule. The standards this format inherits, and which
sections, are listed at the top of the specification; nothing here restates
them.

A REAL FILE TO CHECK AGAINST

  ${origin}/demo/${demo.generatedFrom}
  ${demo.bytes.toLocaleString()} bytes, ${demo.commentCount} OpusTags comments,
  ${Object.keys(demo.speakers).length} speakers, ${demo.transcript?.wordCount} word-timed items.
  How it was made: ${origin}/demo/README.md
`);

	parts.push(rule('WHAT A REAL FILE ACTUALLY CONTAINS'));
	parts.push(
		`Every comment in the demo file, in the order ffprobe reports them.\n` +
			`Payload chunk values are elided; one is shown in full-ish so the shape is clear.\n\n` +
			Object.entries(demo.readableTags)
				.map(([k, v]) => `${k}=${v}`)
				.join('\n') +
			`\n\n${demo.sampleChunkTag?.key}=${demo.sampleChunkTag?.value.slice(0, 72)}…` +
			`\n… and ${demo.chunkTagCount - 1} more chunk tags.\n\n` +
			`Note the ASCII sort order, and that CASSINI_FORMAT is not the first comment.\n` +
			`Note that ffprobe renames DESCRIPTION to "comment", and that Ogg carries\n` +
			`comments on the STREAM, so -show_entries format_tags returns nothing.`
	);

	parts.push(rule('THE DECODED MANIFEST OF THAT FILE'));
	parts.push(JSON.stringify(demo.manifest, null, 2));

	parts.push(rule('THE FIRST ITEMS OF ITS TRANSCRIPT BODY'));
	parts.push(
		JSON.stringify(
			{ format: 'cassini.words.v1', wordCount: demo.transcript?.wordCount, items: demo.firstWords },
			null,
			2
		)
	);

	parts.push(rule('SPECIFICATION — SPEC.md'));
	parts.push(await readRepoFile('SPEC.md'));

	parts.push(rule('TRANSCRIPT BODY — spec/cassini-words-v1.md'));
	parts.push(await readRepoFile('spec/cassini-words-v1.md'));

	parts.push(rule('AUDIO DIGEST — spec/cassini-opus-audio-integrity-v1.md'));
	parts.push(await readRepoFile('spec/cassini-opus-audio-integrity-v1.md'));

	parts.push(rule('GUIDE — writing a file'));
	parts.push(await siteContent('produce'));

	parts.push(rule('GUIDE — reading a file'));
	parts.push(await siteContent('consume'));

	parts.push(rule('GUIDE — checking a file'));
	parts.push(await siteContent('verify'));

	parts.push(rule('IMPLEMENTATION PATHS AND CONFORMANCE SETUP'));
	parts.push(await siteContent('build'));

	for (const s of await listSchemas()) {
		parts.push(rule(`SCHEMA — ${s.file}`));
		parts.push(await readRepoFile(`spec/${s.file}`));
	}

	parts.push(rule('REFERENCE IMPLEMENTATIONS'));
	parts.push(
		`All CC0. Read them if the prose above left you guessing; report it if it did.\n\n` +
			`  ${site.repo}/blob/main/tools/cassini-read.js      browser reader, no dependencies\n` +
			`  ${site.repo}/blob/main/tools/cassini-read-pure.py  reader with no external tools at all\n` +
			`  ${site.repo}/blob/main/tools/cassini-pack.py      complete producer, stdlib only\n` +
			`  ${site.repo}/blob/main/tools/cassini-opus-digest.py  the audio digest alone\n` +
			`  ${site.repo}/blob/main/tools/cassini-extract.py   decode via ffprobe\n\n` +
			`cassini-pack.py and cassini-opus-digest.py were written from the documents\n` +
			`above and nothing else, as a test of whether they are sufficient. The digest\n` +
			`one agrees with the reference Go producer byte for byte on the demo file.\n\n` +
			`The reference implementation, which records and transcribes: ${site.implRepo} (AGPL-3.0)\n`
	);

	// REPO is only referenced to make the dependency explicit for the build.
	void REPO;
	return new Response(parts.join(''));
}
