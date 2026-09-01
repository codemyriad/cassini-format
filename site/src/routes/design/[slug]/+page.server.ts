import { error } from '@sveltejs/kit';
import { renderMarkdownFile } from '$lib/markdown';
import { listDesignDocs } from '$lib/docs';
import { site } from '$lib/site';

export async function entries() {
	return (await listDesignDocs()).map((d) => ({ slug: d.slug }));
}

export async function load({ params }) {
	const docs = await listDesignDocs();
	const doc = docs.find((d) => d.slug === params.slug);
	if (!doc) throw error(404, 'No such design note');

	const rendered = await renderMarkdownFile(doc.file);
	return {
		title: rendered.title || doc.title,
		date: doc.date,
		html: rendered.html,
		headings: rendered.headings,
		source: doc.file,
		sourceHref: `${site.repo}/blob/main/${doc.file}`
	};
}
