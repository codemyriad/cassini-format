import { renderMarkdown } from '$lib/markdown';
import { readRepoFile, stripDocHeader } from '$lib/docs';
import { site } from '$lib/site';

export async function load() {
	// CHANGELOG.md opens with an H1 and no Date:/Status: block. The page header
	// carries the title, so the body starts at the first paragraph.
	const { body } = stripDocHeader(await readRepoFile('CHANGELOG.md'));
	const { html, headings } = await renderMarkdown(body, 'CHANGELOG.md');
	return {
		html,
		headings,
		source: 'CHANGELOG.md',
		sourceHref: `${site.repo}/blob/main/CHANGELOG.md`
	};
}
