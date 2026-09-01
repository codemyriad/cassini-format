import { listSchemas } from '$lib/docs';
import { highlight } from '$lib/markdown';
import { readRepoFile } from '$lib/docs';

export async function load() {
	const schemas = await listSchemas();
	const v3 = await readRepoFile('spec/cassini-portable-meeting-manifest-v1.schema.json');
	const head = JSON.stringify(JSON.parse(v3), null, 2).split('\n').slice(0, 18).join('\n') + '\n  …';
	return { schemas, headHtml: await highlight(head, 'json') };
}
