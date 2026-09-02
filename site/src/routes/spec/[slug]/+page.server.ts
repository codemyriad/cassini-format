import { error } from '@sveltejs/kit';
import { renderMarkdown, renderMarkdownFile } from '$lib/markdown';
import { splitSpec, stripDocHeader, readRepoFile } from '$lib/docs';
import { site } from '$lib/site';

type Page = {
	title: string;
	kicker: string;
	lede: string;
	source: string;
	meta: { label: string; value: string }[];
	markdown: () => Promise<string>;
};

const SPEC_SOURCE = `${site.repo}/blob/main/SPEC.md`;

export const entries = () => [
	{ slug: 'v1' },
	{ slug: 'document' },
	{ slug: 'words-v1' },
	{ slug: 'audio-integrity' }
];

const PAGES: Record<string, Page> = {
	v1: {
		title: 'Cassini portable meeting, version 1',
		kicker: 'Specification · current',
		lede: 'What a producer writes and a consumer reads: the container, the tags, the manifest, and what a reader owes the person in front of it. The whole document, rationale included.',
		source: 'SPEC.md',
		meta: [
			{ label: 'Wire id', value: 'org.cassini.portable-meeting/1' },
			{ label: 'Status', value: 'published 2026-09-02' },
			{ label: 'Media type', value: 'audio/ogg' }
		],
		markdown: async () => (await splitSpec()).raw
	},
	// The same document at its older address. Kept so that links do not break.
	document: {
		title: 'Cassini portable meeting, version 1',
		kicker: 'Specification · current',
		lede: 'The specification, whole. The same page as /spec/v1/.',
		source: 'SPEC.md',
		meta: [{ label: 'Wire id', value: 'org.cassini.portable-meeting/1' }],
		markdown: async () => (await splitSpec()).raw
	},
	'words-v1': {
		title: 'The transcript body',
		kicker: 'Specification · cassini.words.v1',
		lede: 'Where the timestamps live: one item per word, pointing at a speaker. Each transcript in a file has its own chunk set carrying one of these.',
		source: 'spec/cassini-words-v1.md',
		meta: [
			{ label: 'Format id', value: 'cassini.words.v1' },
			{ label: 'Media type', value: 'application/vnd.cassini.transcript-words+json' }
		],
		markdown: async () => ''
	},
	'audio-integrity': {
		title: 'The audio digest',
		kicker: 'Specification · exact-opus-audio-v1',
		lede: 'The byte rule for hashing an Opus stream, written so rewriting the tags cannot change the answer. It is what makes a recording\u2019s identity survive reprocessing.',
		source: 'spec/cassini-opus-audio-integrity-v1.md',
		meta: [{ label: 'Policy id', value: 'exact-opus-audio-v1' }],
		markdown: async () => ''
	}
};

export async function load({ params }) {
	const page = PAGES[params.slug];
	if (!page) throw error(404, 'No such specification version');

	// The two standalone spec documents get the same header treatment as the
	// sections cut out of SPEC.md: title and status in the page header, not twice.
	const standalone =
		params.slug === 'audio-integrity'
			? 'spec/cassini-opus-audio-integrity-v1.md'
			: params.slug === 'words-v1'
				? 'spec/cassini-words-v1.md'
				: '';

	const extraMeta: { label: string; value: string }[] = [];
	const rendered = standalone
		? await (async () => {
				const { meta, body } = stripDocHeader(await readRepoFile(standalone));
				extraMeta.push(...meta);
				return renderMarkdown(body, standalone);
			})()
		: await renderMarkdown(await page.markdown(), 'SPEC.md');

	return {
		slug: params.slug,
		title: page.title,
		kicker: page.kicker,
		lede: page.lede,
		meta: [...page.meta, ...extraMeta],
		source: page.source,
		sourceHref: page.source === 'SPEC.md' ? SPEC_SOURCE : `${site.repo}/blob/main/${page.source}`,
		html: rendered.html,
		headings: rendered.headings
	};
}
