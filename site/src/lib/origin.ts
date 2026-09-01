import { base } from '$app/paths';

/**
 * The site's public URL, for the two plain-text files that get handed to a model
 * or pasted somewhere the host is lost.
 *
 * The deploy target is not decided, so this defaults to relative paths, which
 * are correct everywhere. Set SITE_URL at build time to make them absolute:
 *
 *   SITE_URL=https://example.com npm run build
 *
 * At prerender time SvelteKit reports url.origin as http://sveltekit-prerender,
 * which must never reach a published file.
 */
const configured = (process.env.SITE_URL ?? '').replace(/\/+$/, '');

export const origin = configured || base;
export const absolute = (path: string) => `${origin}${path}`;
