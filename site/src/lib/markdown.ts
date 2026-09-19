import { readFile } from 'node:fs/promises';
import path from 'node:path';
import matter from 'gray-matter';
import { unified } from 'unified';
import remarkParse from 'remark-parse';
import remarkGfm from 'remark-gfm';
import remarkRehype from 'remark-rehype';
import rehypeRaw from 'rehype-raw';
import rehypeSlug from 'rehype-slug';
import rehypeAutolinkHeadings from 'rehype-autolink-headings';
import rehypeStringify from 'rehype-stringify';
import rehypeShiki from '@shikijs/rehype';
import { visit } from 'unist-util-visit';

/** The repo root: the site lives in site/, the canonical documents live above it. */
export const REPO = path.resolve(process.cwd(), '..');

export type Heading = { depth: number; id: string; text: string };

/**
 * The design notes the site publishes, in order. The others in design/ are
 * historical: they stay in the repository, and a link to one from a rendered
 * document has to point there rather than at a route that does not exist.
 */
export const PUBLISHED_DESIGN = [
	'packet-digest',
	'multi-transcription',
	'operator-sealing',
	'format-simplification-2026-09-07'
];

/**
 * SPEC.md and design/*.md link to each other as relative repo paths so they stay
 * navigable on GitHub. On the site those paths have to become routes. Anything
 * we do not recognise is left alone, and the prerenderer will shout if it 404s.
 */
function rewriteHref(href: string): string | null {
	// Absolute URLs, in-page anchors, protocol-relative and site-absolute paths
	// are already correct. Only repository-relative paths need rewriting.
	if (/^([a-z][a-z0-9+.-]*:|#|\/)/i.test(href)) return null;
	const [rawPath, hash = ''] = href.split('#');
	const anchor = hash ? `#${hash}` : '';
	if (!rawPath) return null;

	const file = rawPath.split('/').pop()!;
	const inSpecDir = /(^|\/)spec\//.test(rawPath);

	if (file.endsWith('.schema.json')) return `/schema/${file}`;
	if (file === 'SPEC.md') return `/spec/document/${anchor}`;
	if (file === 'README.md') return `/${anchor}`;
	if (file === 'CHANGELOG.md') return `/changelog/${anchor}`;
	// The two standalone spec documents have shorter route names than filenames.
	if (file === 'cassini-opus-audio-integrity-v1.md') return `/spec/audio-integrity/${anchor}`;
	if (file === 'cassini-words-v1.md') return `/spec/words-v1/${anchor}`;
	const clean = rawPath.replace(/^\.\//, '');
	if (file.endsWith('.md')) {
		const slug = file.slice(0, -3);
		if (!inSpecDir && !PUBLISHED_DESIGN.includes(slug)) {
			return `https://github.com/codemyriad/cassini-format/blob/main/${clean}`;
		}
		return `/${inSpecDir ? 'spec' : 'design'}/${slug}/${anchor}`;
	}
	// Source files and fixtures stay pointing at the repository.
	if (/\.(py|txt|json|go|js|mjs|ts|sh)$/.test(file)) {
		return `https://github.com/codemyriad/cassini-format/blob/main/${clean}`;
	}
	// A directory link (no extension, or a trailing slash) is a repo tree.
	if (rawPath.endsWith('/') || !file.includes('.')) {
		return `https://github.com/codemyriad/cassini-format/tree/main/${clean.replace(/\/$/, '')}`;
	}
	return null;
}

function rehypeRewriteLinks() {
	return (tree: unknown) => {
		visit(tree as never, 'element', (node: never) => {
			const el = node as { tagName: string; properties?: Record<string, unknown> };
			if (el.tagName !== 'a' || !el.properties) return;
			const href = el.properties.href;
			if (typeof href !== 'string') return;
			const next = rewriteHref(href);
			if (next) el.properties.href = next;
			else if (/^https?:/i.test(href)) {
				el.properties.rel = 'noreferrer';
			}
		});
	};
}

/** Collect headings for a table of contents, after rehype-slug has assigned ids. */
function rehypeCollectHeadings(sink: Heading[]) {
	return (tree: unknown) => {
		visit(tree as never, 'element', (node: never) => {
			const el = node as {
				tagName: string;
				properties?: Record<string, unknown>;
				children?: unknown[];
			};
			const m = /^h([2-4])$/.exec(el.tagName);
			if (!m || !el.properties?.id) return;
			const text = textOf(el.children ?? []);
			sink.push({ depth: Number(m[1]), id: String(el.properties.id), text });
		});
	};
}

function textOf(children: unknown[]): string {
	let out = '';
	for (const child of children) {
		const c = child as { type?: string; value?: string; children?: unknown[]; tagName?: string };
		if (c.type === 'text') out += c.value ?? '';
		// Skip the anchor link rehype-autolink-headings injects.
		else if (c.children && c.tagName !== 'a') out += textOf(c.children);
	}
	return out.trim();
}

/** hast stores a class list as className[], but plugins are inconsistent about it. */
function languageOf(properties?: Record<string, unknown>): string {
	const raw = properties?.className ?? properties?.class;
	const classes = Array.isArray(raw) ? raw.map(String) : String(raw ?? '').split(/\s+/);
	return classes.find((c) => c.startsWith('language-'))?.slice(9) ?? '';
}

/** Wrap every top-level code block so it gets the site's chrome and a copy button. */
function rehypeFrameCode() {
	return (tree: unknown) => {
		visit(tree as never, 'element', (node: never, index: number | undefined, parent: never) => {
			const el = node as { tagName: string; properties?: Record<string, unknown> };
			const p = parent as { type?: string; children?: unknown[] } | undefined;
			// Tables can scroll horizontally on small screens. Preserve their table
			// semantics while allowing keyboard users to focus and scroll them.
			if (el.tagName === 'table') {
				el.properties = { ...el.properties, tabIndex: 0 };
			}
			if (el.tagName !== 'pre' || !p || index === undefined) return;
			const holder = p as { children: unknown[] };
			if ((holder as { tagName?: string }).tagName === 'div') return;
			// addLanguageClass puts the class on the <code>, not the <pre>.
			const code = ((node as { children?: unknown[] }).children ?? []).find(
				(c) => (c as { tagName?: string }).tagName === 'code'
			) as { properties?: Record<string, unknown> } | undefined;
			const lang = languageOf(code?.properties);
			// A console block is output, not something you run. It gets a quieter
			// frame and no copy button.
			const isOutput = lang === 'console';
			holder.children[index] = {
				type: 'element',
				tagName: 'div',
				properties: { class: isOutput ? 'code code--out' : 'code', 'data-lang': lang },
				children: [
					{
						type: 'element',
						tagName: 'div',
						properties: { class: 'code__bar' },
						children: [
							{
								type: 'element',
								tagName: 'span',
								properties: {},
								children: [{ type: 'text', value: isOutput ? 'output' : lang || 'text' }]
							},
							...(isOutput
								? []
								: [
										{
											type: 'element',
											tagName: 'button',
											properties: { class: 'copy', type: 'button', 'data-copy': '' },
											children: [{ type: 'text', value: 'copy' }]
										}
									])
						]
					},
					node
				]
			};
		});
	};
}

export type Rendered = {
	html: string;
	headings: Heading[];
	data: Record<string, unknown>;
	title: string;
	source: string;
};

export async function renderMarkdownFile(
	repoRelative: string,
	options: { anchorFallback?: string } = {}
): Promise<Rendered> {
	const raw = await readFile(path.join(REPO, repoRelative), 'utf8');
	return renderMarkdown(raw, repoRelative, options);
}

/**
 * Splitting SPEC.md into pages breaks its internal cross-references: a part can
 * link to a heading that lives in another part. Rather than editing the
 * document, any in-page anchor that does not exist on the rendered
 * page is pointed at the full-document page, where every heading does exist.
 */
function reanchor(html: string, fallback: string): string {
	const ids = new Set([...html.matchAll(/\sid="([^"]+)"/g)].map((m) => m[1]));
	return html.replace(/href="#([^"]+)"/g, (whole, id: string) =>
		ids.has(decodeURIComponent(id)) ? whole : `href="${fallback}#${id}"`
	);
}

export async function renderMarkdown(
	raw: string,
	source = '',
	options: { anchorFallback?: string } = {}
): Promise<Rendered> {
	const { content, data } = matter(raw);
	const headings: Heading[] = [];

	const file = await unified()
		.use(remarkParse)
		.use(remarkGfm)
		.use(remarkRehype, { allowDangerousHtml: true })
		.use(rehypeRaw)
		.use(rehypeSlug)
		.use(rehypeCollectHeadings, headings)
		.use(rehypeAutolinkHeadings, {
			behavior: 'append',
			properties: { class: 'anchor', ariaHidden: 'true', tabIndex: -1 },
			content: { type: 'text', value: '#' }
		})
		.use(rehypeRewriteLinks)
		.use(rehypeShiki, {
			themes: { light: 'github-light-high-contrast', dark: 'github-dark-default' },
			defaultColor: false,
			cssVariablePrefix: '--shiki-',
			// Shiki replaces the <pre> outright, so this is the only way the
			// language survives to the chrome that wraps it below.
			addLanguageClass: true
		})
		.use(rehypeFrameCode)
		.use(rehypeStringify, { allowDangerousHtml: true })
		.process(content);

	const firstH1 = /^#\s+(.+)$/m.exec(content);
	const html = options.anchorFallback
		? reanchor(String(file), options.anchorFallback)
		: String(file);
	return {
		html,
		headings,
		data: data as Record<string, unknown>,
		title: String(data.title ?? firstH1?.[1] ?? ''),
		source
	};
}

/** Highlight a standalone snippet with the same theme the prose uses. */
export async function highlight(code: string, lang: string): Promise<string> {
	const { codeToHtml } = await import('shiki');
	return codeToHtml(code.replace(/\n$/, ''), {
		lang,
		themes: { light: 'github-light-high-contrast', dark: 'github-dark-default' },
		defaultColor: false,
		cssVariablePrefix: '--shiki-'
	});
}
