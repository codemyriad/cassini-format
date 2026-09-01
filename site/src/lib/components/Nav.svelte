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
</script>

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

		<nav class="nav__links" class:nav__links--open={open} aria-label="Main">
			{#each nav as item (item.href)}
				<a
					href="{base}{item.href}"
					aria-current={current.startsWith(item.href.replace(/v3\/$/, '')) ? 'page' : undefined}
					class:on={current.startsWith(item.href.replace(/v3\/$/, ''))}
					onclick={() => (open = false)}>{item.label}</a
				>
			{/each}
			<a href={site.repo} rel="noreferrer">GitHub<span class="ext">↗</span></a>
		</nav>

		<div class="nav__end">
			<button class="ghost" type="button" onclick={toggleTheme} aria-label="Switch colour theme">
				{theme === 'dark' ? 'light' : 'dark'}
			</button>
			<button
				class="ghost burger"
				type="button"
				aria-expanded={open}
				onclick={() => (open = !open)}>menu</button
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
		height: 52px;
	}
	.brand {
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
		font-size: 13px;
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
	}
	.ghost {
		font: inherit;
		font-size: 11px;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		color: var(--fg-4);
		background: var(--bg-raise);
		border: 1px solid var(--rule);
		padding: 0.28rem 0.55rem;
		cursor: pointer;
	}
	.ghost:hover {
		color: var(--fg);
		border-color: var(--rule-hi);
	}
	.burger {
		display: none;
	}

	@media (max-width: 820px) {
		.burger {
			display: inline-block;
		}
		.nav__links {
			display: none;
			position: absolute;
			top: 52px;
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
			padding: 0.5rem 0;
			width: 100%;
			border-bottom: 1px solid var(--rule);
		}
	}
</style>
