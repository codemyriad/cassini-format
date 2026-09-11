<script lang="ts">
	import { page } from '$app/state';
	import { base } from '$app/paths';
	import { nav, site } from '$lib/site';

	let open = $state(false);
	let theme = $state<'dark' | 'light'>('dark');

	function toggleTheme() {
		theme = theme === 'dark' ? 'light' : 'dark';
		document.documentElement.dataset.theme = theme;
		try {
			localStorage.setItem('cassini-theme', theme);
		} catch {
			/* private mode; the page still works, it just forgets */
		}
	}

	$effect(() => {
		theme = (document.documentElement.dataset.theme as 'dark' | 'light') ?? 'dark';
	});

	const current = $derived(page.url.pathname);
	const isCurrent = (href: string) =>
		current.startsWith(`${base}${href}`) ||
		(href === '/using/' && current.startsWith(`${base}/status/`)) ||
		(href === '/build/' &&
			['/consume/', '/produce/', '/verify/'].some((path) => current.startsWith(`${base}${path}`))) ||
		(href === '/try/' && current.startsWith(`${base}/demo/`)) ||
		(href === '/spec/' &&
			['/schema/', '/design/'].some((path) => current.startsWith(`${base}${path}`)));
</script>

<svelte:window
	onkeydown={(event) => {
		if (event.key === 'Escape' && open) {
			open = false;
			document.getElementById('menu-toggle')?.focus();
		}
	}}
/>

<header class="nav">
	<div class="shell nav__in">
		<a class="brand" href="{base}/" aria-label="{site.name} portable meeting format, home">
			<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
				<circle cx="12" cy="12" r="5" fill="none" stroke="currentColor" stroke-width="1.6" />
				<ellipse
					cx="12"
					cy="12"
					rx="10.4"
					ry="3.6"
					fill="none"
					stroke="currentColor"
					stroke-width="1.3"
					transform="rotate(-19 12 12)"
					opacity="0.75"
				/>
			</svg>
			<span>{site.name}</span><span class="brand__dim">/format</span>
		</a>

		<nav id="main-navigation" class="nav__links" class:nav__links--open={open} aria-label="Main">
			{#each nav as item (item.href)}
				<a
					href="{base}{item.href}"
					aria-current={isCurrent(item.href)
						? current === `${base}${item.href}` ? 'page' : 'location'
						: undefined}
					class:on={isCurrent(item.href)}
					onclick={() => (open = false)}>{item.label}</a
				>
			{/each}
			<a href={site.repo} rel="noreferrer">GitHub<span class="ext">↗</span></a>
		</nav>

		<div class="nav__end">
			<button
				class="ghost theme"
				type="button"
				onclick={toggleTheme}
				aria-label="Switch to {theme === 'dark' ? 'light' : 'dark'} theme"
				title="Switch colour theme"
			>
				{#if theme === 'dark'}
					<svg
						width="18"
						height="18"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="1.5"
						aria-hidden="true"
						><circle cx="12" cy="12" r="4" /><path
							d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5"
						/></svg
					>
				{:else}
					<svg
						width="18"
						height="18"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="1.5"
						aria-hidden="true"><path d="M20.5 14A9 9 0 0 1 10 3.5 9 9 0 1 0 20.5 14Z" /></svg
					>
				{/if}
			</button>
			<button
				class="ghost burger"
				id="menu-toggle"
				type="button"
				aria-expanded={open}
				aria-controls="main-navigation"
				onclick={() => (open = !open)}>{open ? 'Close' : 'Menu'}</button
			>
		</div>
	</div>
</header>

<style>
	.nav {
		position: sticky;
		top: 0;
		z-index: 40;
		background: color-mix(in srgb, var(--bg) 88%, transparent);
		backdrop-filter: blur(10px);
		border-bottom: 1px solid var(--rule);
	}
	.nav__in {
		display: flex;
		align-items: center;
		gap: 1.5rem;
		height: 72px;
	}
	.brand {
		font-family: var(--mono);
		font-size: 15px;
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		color: var(--fg);
		font-weight: 600;
		letter-spacing: -0.01em;
		flex: none;
	}
	.brand:hover {
		text-decoration: none;
		color: var(--blue);
	}
	.brand svg {
		color: var(--blue);
	}
	.brand__dim {
		color: var(--fg-4);
		font-weight: 400;
	}
	.nav__links {
		display: flex;
		align-items: center;
		gap: 1.35rem;
		margin-left: auto;
		font-size: 14px;
	}
	.nav__links a {
		color: var(--fg-3);
	}
	.nav__links a:hover,
	.nav__links a.on {
		color: var(--fg);
		text-decoration: none;
	}
	.nav__links a.on {
		text-decoration: underline;
		text-decoration-color: var(--blue);
		text-underline-offset: 6px;
	}
	.ext {
		color: var(--fg-5);
		margin-left: 0.25rem;
		font-size: 10px;
	}
	.nav__end {
		display: flex;
		gap: 0.35rem;
		flex: none;
		margin-left: auto;
	}
	.ghost {
		font: inherit;
		font-size: 11px;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		color: var(--fg-4);
		background: var(--bg-raise);
		border: 1px solid var(--rule);
		padding: 0.5rem 0.7rem;
		min-height: 40px;
		min-width: 40px;
		border-radius: 4px;
		cursor: pointer;
	}
	.ghost:hover {
		color: var(--fg);
		border-color: var(--rule-hi);
	}
	.burger {
		display: none;
	}
	.theme {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}

	@media (max-width: 820px) {
		.burger {
			display: inline-block;
		}
		.nav__links {
			display: none;
			position: absolute;
			top: 72px;
			left: 0;
			right: 0;
			flex-direction: column;
			align-items: flex-start;
			gap: 0;
			background: var(--bg);
			border-bottom: 1px solid var(--rule);
			padding: 0.5rem var(--pad) 1rem;
		}
		.nav__links--open {
			display: flex;
		}
		.nav__links a {
			padding: 0.75rem 0;
			width: 100%;
			border-bottom: 1px solid var(--rule);
		}
	}
	@media (max-width: 380px) {
		.nav__in {
			gap: 0.75rem;
		}
		.brand__dim {
			display: none;
		}
	}
</style>
