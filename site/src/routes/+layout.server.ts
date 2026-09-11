import { base } from '$app/paths';
import { absolute, origin } from '$lib/origin';
import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = ({ url }) => ({
	canonical: /^https?:\/\//.test(origin) ? absolute(url.pathname.slice(base.length)) : null
});
