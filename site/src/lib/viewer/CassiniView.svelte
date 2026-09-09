<script lang="ts">
	import { mount, unmount } from 'svelte';
	import MeetingView from '../vendor/cassini-viewer/src/components/MeetingView.svelte';
	import type { LoadedArtifact } from '../vendor/cassini-viewer/src/viewer/loadArtifact';
	import { singleArtifactProvider } from './artifact';
	import viewerCss from './viewer.css?inline';
	import embeddingCss from './embedding.css?inline';

	let {
		artifact,
		compact = false,
		onplaybackerror
	}: {
		artifact: LoadedArtifact;
		compact?: boolean;
		onplaybackerror: (message: string) => void;
	} = $props();
	let host: HTMLDivElement;

	$effect(() => {
		const current = artifact;
		const isCompact = compact;
		const shadow = host.shadowRoot ?? host.attachShadow({ mode: 'open' });
		const styles = document.createElement('style');
		styles.textContent = viewerCss + embeddingCss;
		const target = document.createElement('div');
		target.className = `cassini-root${isCompact ? ' compact' : ''}`;
		const syncTheme = () => {
			target.dataset.theme =
				document.documentElement.dataset.theme === 'light' ? 'saturn-light' : 'saturn-dark';
		};
		syncTheme();
		const observer = new MutationObserver(syncTheme);
		observer.observe(document.documentElement, {
			attributes: true,
			attributeFilter: ['data-theme']
		});
		shadow.replaceChildren(styles, target);
		const instance = mount(MeetingView, {
			target,
			props: {
				dataProvider: singleArtifactProvider(current),
				bundled: true,
				contained: true,
				isDesktop: true,
				prefersReducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches
			},
			events: { playbackerror: (event: CustomEvent<string>) => onplaybackerror(event.detail) }
		});
		const scrollPane = target.querySelector<HTMLElement>('.meeting-viewer > div');
		if (scrollPane) {
			scrollPane.tabIndex = 0;
			scrollPane.setAttribute('role', 'region');
			scrollPane.setAttribute('aria-label', 'Scrollable transcript. Space to play or pause.');
		}
		return () => {
			observer.disconnect();
			void unmount(instance);
		};
	});
</script>

<!-- Shadow DOM isolates Cassini's own stylesheet from the format site's UI. -->
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
</style>
