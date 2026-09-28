/**
 * The Cassini viewer this site shows recordings in: gocassini's published
 * `<cassini-meeting>` embed (its contract is gocassini's
 * `cassini-viewer/ATTRIBUTES.md`), loaded the way any page loads it.
 *
 * Pinned to one exact release rather than the moving `/embed/v1/` channel, so
 * the site keeps showing the viewer it was checked against. Move to a newer
 * viewer by changing the version here.
 *
 * `VITE_CASSINI_EMBED_SRC` points a local build at another copy of the embed,
 * for example one built from a gocassini checkout.
 */
export const CASSINI_EMBED_VERSION = 'main-ac7ff29b';

export const CASSINI_EMBED_SRC: string =
	import.meta.env.VITE_CASSINI_EMBED_SRC ||
	`https://dist.gocassini.com/embed/${CASSINI_EMBED_VERSION}/viewer.js`;

let loading: Promise<void> | null = null;

/** Add the embed's script to the page once; resolves when the element is defined. */
export function loadCassiniEmbed(): Promise<void> {
	if (customElements.get('cassini-meeting')) return Promise.resolve();
	loading ??= new Promise<void>((resolve, reject) => {
		const script = document.createElement('script');
		script.src = CASSINI_EMBED_SRC;
		script.onload = () => resolve();
		script.onerror = () => {
			loading = null;
			script.remove();
			reject(new Error(`could not load ${CASSINI_EMBED_SRC}`));
		};
		document.head.appendChild(script);
	});
	return loading;
}
