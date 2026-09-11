import { loadContent } from '$lib/content';

export async function load() {
	const { html, headings } = await loadContent('build');
	return { html, headings };
}
