<script lang="ts">
	import { loadCassiniEmbed } from './embed';

	let {
		src,
		title = '',
		compact = false,
		onplaybackerror,
		onunavailable
	}: {
		/** URL of the recording; a blob URL for bytes the page has already read. */
		src: string;
		title?: string;
		compact?: boolean;
		onplaybackerror: (message: string) => void;
		onunavailable: (message: string) => void;
	} = $props();
	let host: HTMLDivElement;

	// Built by hand rather than in markup, so every attribute is on the element
	// before it connects: the embed reads its attributes on arrival.
	$effect(() => {
		const recording = src;
		const name = title;
		let element: HTMLElement | null = null;
		let observer: MutationObserver | null = null;
		let cancelled = false;
		const onError = (event: Event) =>
			onplaybackerror((event as CustomEvent<{ message: string }>).detail.message);

		loadCassiniEmbed().then(
			() => {
				if (cancelled) return;
				element = document.createElement('cassini-meeting');
				element.setAttribute('src', recording);
				if (name) element.setAttribute('title', name);
				// The page around the player names the recording and shows the file's
				// details, so the viewer keeps to the transcript and the player.
				element.setAttribute('layout', 'inline');
				// Files opened on /try may come from any producer, not only Cassini.
				element.setAttribute('hide-badge', '');
				const syncTheme = () =>
					element?.setAttribute(
						'theme',
						document.documentElement.dataset.theme === 'light' ? 'light' : 'dark'
					);
				syncTheme();
				observer = new MutationObserver(syncTheme);
				observer.observe(document.documentElement, {
					attributes: true,
					attributeFilter: ['data-theme']
				});
				element.addEventListener('playbackerror', onError);
				host.replaceChildren(element);
			},
			() => {
				if (!cancelled) onunavailable('The Cassini viewer could not be loaded.');
			}
		);
		return () => {
			cancelled = true;
			observer?.disconnect();
			element?.removeEventListener('playbackerror', onError);
			element?.remove();
		};
	});
</script>

<div
	class="cassini-host"
	class:compact
	bind:this={host}
	aria-label="Cassini audio and transcript viewer"
></div>

<style>
	.cassini-host {
		height: 480px;
		min-width: 0;
	}
	.compact {
		height: 350px;
	}
	/* The embed's styling contract: its palette and font, from the site's own. */
	.cassini-host :global(cassini-meeting) {
		display: block;
		height: 100%;
		--cassini-color-base-100: var(--bg);
		--cassini-color-base-200: var(--bg);
		--cassini-color-base-300: var(--rule);
		--cassini-color-base-content: var(--fg-2);
		--cassini-color-primary: var(--blue);
		--cassini-color-primary-content: var(--bg);
		--cassini-font-sans: var(--sans, system-ui, sans-serif);
	}
</style>
