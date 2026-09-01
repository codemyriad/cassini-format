<script lang="ts">
	import '../app.css';
	import Nav from '$lib/components/Nav.svelte';
	import Footer from '$lib/components/Footer.svelte';

	let { children } = $props();

	// One delegated listener for every copy button the markdown pipeline emits.
	$effect(() => {
		const onClick = async (event: MouseEvent) => {
			const button = (event.target as HTMLElement)?.closest('[data-copy]');
			if (!(button instanceof HTMLElement)) return;
			const code = button.closest('.code')?.querySelector('pre')?.textContent ?? '';
			try {
				await navigator.clipboard.writeText(code);
				const previous = button.textContent;
				button.textContent = 'copied';
				setTimeout(() => (button.textContent = previous), 1200);
			} catch {
				button.textContent = 'select it';
			}
		};
		document.addEventListener('click', onClick);
		return () => document.removeEventListener('click', onClick);
	});
</script>

<a class="skip" href="#main">Skip to content</a>
<Nav />
<main id="main">{@render children()}</main>
<Footer />

<style>
	.skip {
		position: absolute;
		left: -9999px;
		top: 0;
		background: var(--bg);
		border: 1px solid var(--blue);
		padding: 0.6rem 1rem;
		z-index: 100;
	}
	.skip:focus {
		left: 1rem;
		top: 1rem;
	}
</style>
