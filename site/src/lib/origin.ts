import { base } from '$app/paths';

/**
 * The site's public URL, for the two plain-text files that get handed to a model
 * or pasted somewhere the host is lost.
 *
 * The site lives at https://format.gocassini.com. Without SITE_URL
 * the build falls back to relative paths, which are correct on any preview
 * host. The published build sets it:
 *
 *   SITE_URL=https://format.gocassini.com npm run build
 *
 * At prerender time SvelteKit reports url.origin as http://sveltekit-prerender,
 * which must never reach a published file.
 */
const configured = (process.env.SITE_URL ?? '').replace(/\/+$/, '');

export const origin = configured || base;
export const absolute = (path: string) => `${origin}${path}`;
