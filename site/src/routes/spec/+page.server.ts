import { listSchemas } from '$lib/docs';

export async function load() {
	return { schemas: await listSchemas() };
}
