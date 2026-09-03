import { readFile, readdir } from 'node:fs/promises';
import path from 'node:path';
import { REPO } from '$lib/markdown';

/**
 * SPEC.md is one document sorted into machinery, the current version, and the
 * versions before it. The per-version pages are cut out of it at the
 * `<!-- spec:part NAME -->` markers, which markdown renderers ignore, so a
 * heading can be renamed or a section moved without breaking a URL. A part runs
 * from its marker to the next one.
 */
export async function splitSpec() {
	const raw = await readFile(path.join(REPO, 'SPEC.md'), 'utf8');
	const lines = raw.split('\n');
	const cuts: { name: string; at: number }[] = [];
	let fenced = false;
	lines.forEach((line, i) => {
		if (/^```/.test(line)) fenced = !fenced;
		const m = fenced ? null : /^<!--\s*spec:part\s+([a-z0-9-]+)\s*-->\s*$/.exec(line);
		if (m) cuts.push({ name: m[1], at: i });
	});
	const parts = new Map<string, string>();
	cuts.forEach((cut, i) => {
		const end = cuts[i + 1]?.at ?? lines.length;
		parts.set(cut.name, lines.slice(cut.at + 1, end).join('\n').trim());
	});
	return { raw, parts };
}

/**
 * Every document in this repository opens the same way: an H1, then Date: and
 * Status: lines. The site shows all three in the page header, so strip them off
 * the body and hand them back as metadata instead of printing them twice.
 */
export function stripDocHeader(raw: string) {
	const lines = raw.split('\n');
	const title = /^#\s+(.+)$/.exec(lines[0] ?? '')?.[1]?.trim() ?? '';
	let at = title ? 1 : 0;
	const meta: { label: string; value: string }[] = [];
	while (at < lines.length) {
		const line = lines[at].trim();
		if (!line) {
			at++;
			continue;
		}
		const m = /^(Date|Status|Source|Author):\s*(.+)$/.exec(line);
		if (!m) break;
		meta.push({ label: m[1], value: m[2].replace(/\.$/, '') });
		at++;
	}
	return { title, meta, body: lines.slice(at).join('\n').trim() };
}

export type DesignDoc = { slug: string; file: string; title: string; date: string; blurb: string };

/**
 * The design notes the site publishes, in order. Other files in design/ are
 * historical and stay in the repository only.
 */
const DESIGN_ORDER = ['packet-digest', 'multi-transcription', 'operator-sealing'];

export async function listDesignDocs(): Promise<DesignDoc[]> {
	const dir = path.join(REPO, 'design');
	const files = (await readdir(dir)).filter((f) =>
		DESIGN_ORDER.includes(f.replace(/\.md$/, ''))
	);
	const docs = await Promise.all(
		files.map(async (file) => {
			const text = await readFile(path.join(dir, file), 'utf8');
			const title = /^#\s+(.+)$/m.exec(text)?.[1]?.trim() ?? file;
			const date = /^Date(?: of the discussion)?:\s*(.+)$/m.exec(text)?.[1]?.trim() ?? '';
			// First real paragraph, minus the metadata block at the top.
			const body = text
				.split('\n')
				.filter((l) => !/^(#|Date|Status|Source|Author)/.test(l.trim()))
				.join('\n')
				.trim();
			const blurb = (body.split(/\n\s*\n/)[0] ?? '').replace(/\s+/g, ' ').slice(0, 240);
			return { slug: file.slice(0, -3), file: `design/${file}`, title, date, blurb };
		})
	);
	return docs.sort((a, b) => DESIGN_ORDER.indexOf(a.slug) - DESIGN_ORDER.indexOf(b.slug));
}

export async function listSchemas() {
	const dir = path.join(REPO, 'spec');
	const files = (await readdir(dir)).filter((f) => f.endsWith('.schema.json'));
	return Promise.all(
		files.sort().map(async (file) => {
			const text = await readFile(path.join(dir, file), 'utf8');
			const json = JSON.parse(text) as { title?: string; $id?: string; required?: string[] };
			return {
				file,
				bytes: text.length,
				title: json.title ?? file,
				id: json.$id ?? '',
				required: json.required ?? []
			};
		})
	);
}

export const readRepoFile = (rel: string) => readFile(path.join(REPO, rel), 'utf8');
