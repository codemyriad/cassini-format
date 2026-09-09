import { origin } from '$lib/origin';
import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = ({ url }) => ({
	canonical: /^https?:\/\//.test(origin) ? new URL(url.pathname, origin).href : null
});
