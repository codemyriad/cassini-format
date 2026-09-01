import { loadContent } from '$lib/content';

export async function load() {
	const { html, headings } = await loadContent('status');
	return { html, headings };
}
