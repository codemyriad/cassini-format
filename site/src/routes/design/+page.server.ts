import { listDesignDocs } from '$lib/docs';

export async function load() {
	return { docs: await listDesignDocs() };
}
