import { base } from '$app/paths';
import { site } from '$lib/site';

/**
 * The site's public URL, for canonical links and the two plain-text files that
 * get handed to a model or pasted somewhere the host is lost.
 *
 * Builds default to the public site, including BASE_PATH when set. SITE_URL can
 * override the complete site root; an explicitly empty value keeps links
 * relative for a preview that needs to be independent of the public host.
 *
 * At prerender time SvelteKit reports url.origin as http://sveltekit-prerender,
 * which must never reach a published file.
 */
const configured = (process.env.SITE_URL ?? `${site.url}${base}`).replace(/\/+$/, '');

export const origin = configured || base;
export const absolute = (path: string) => `${origin}${path}`;
