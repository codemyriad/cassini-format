import { loadContent } from '$lib/content';

export async function load() {
	const { html, headings } = await loadContent('verify');
	return { html, headings };
}
