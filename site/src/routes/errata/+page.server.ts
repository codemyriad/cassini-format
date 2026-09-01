import { renderMarkdownFile } from '$lib/markdown';
import { stripDocHeader, readRepoFile } from '$lib/docs';
import { site } from '$lib/site';

export async function load() {
	const { meta, body } = stripDocHeader(await readRepoFile('ERRATA.md'));
	const { renderMarkdown } = await import('$lib/markdown');
	const { html, headings } = await renderMarkdown(body, 'ERRATA.md');
	void renderMarkdownFile;
	return { html, headings, meta };
}
