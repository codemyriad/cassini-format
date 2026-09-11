import { base } from '$app/paths';
import { absolute } from '$lib/origin';
import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = ({ url }) => ({
	canonical: absolute(url.pathname.slice(base.length))
});
