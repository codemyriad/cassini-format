import { error } from '@sveltejs/kit';
import { listSchemas, readRepoFile } from '$lib/docs';

export const prerender = true;
export const trailingSlash = 'never';

export async function entries() {
	return (await listSchemas()).map((s) => ({ file: s.file }));
}

export async function GET({ params }) {
	// Only ever serve names the repo actually has; never a path from the URL.
	const known = (await listSchemas()).some((s) => s.file === params.file);
	if (!known) throw error(404, 'No such schema');

	const body = await readRepoFile(`spec/${params.file}`);
	return new Response(body);
}
