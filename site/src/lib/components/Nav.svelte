<script lang="ts">
	import { page } from '$app/state';
	import { base } from '$app/paths';
	import { nav, site } from '$lib/site';

	let open = $state(false);
	let theme = $state<'dark' | 'light'>('light');

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
		theme = (document.documentElement.dataset.theme as 'dark' | 'light') ?? 'light';
	});

	const current = $derived(page.url.pathname);
	// An href with a fragment ('/#implementations') is a section of the home page,
	// never a path of its own, so it never matches a pathname.
	const isCurrent = (href: string) =>
		(!href.includes('#') && current.startsWith(`${base}${href}`)) ||
		(href === '/build/' &&
			['/consume/', '/produce/'].some((path) => current.startsWith(`${base}${path}`))) ||
		(href === '/spec/' &&
			['/schema/', '/design/', '/changelog/'].some((path) =>
				current.startsWith(`${base}${path}`)
			));
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
			<svg class="brand__mark" viewBox="0 38 180 104" width="35" height="20" aria-hidden="true">
				<path d="M138.25 97.5879C134.82 121.014 114.644 139 90.2658 139C81.3703 139 74.433 137.18 67.2658 133C94.2658 124 115.766 112.5 138.25 97.5879Z" fill="currentColor" fill-opacity="0.7" />
				<path d="M165.266 52C186.39 51.5506 178.266 65.5 165.266 75.5C162.422 77.6875 158.956 80.0667 154.999 82.5742L154.438 82.9248C146.528 87.9039 136.723 93.3741 126.033 98.8506C121.081 101.387 115.939 103.924 110.708 106.415C108.501 107.466 106.278 108.509 104.046 109.54C102.622 110.198 101.195 110.853 99.7656 111.5C96.9458 112.777 94.08 113.989 91.1895 115.142C90.2297 115.524 89.2674 115.901 88.3027 116.271C87.6569 116.518 87.0098 116.762 86.3623 117.003C84.8195 117.578 83.2726 118.136 81.7246 118.678C76.9192 120.36 72.1032 121.882 67.3652 123.256C65.9608 123.663 64.5633 124.057 63.1748 124.438C61.3061 124.951 59.454 125.441 57.624 125.907C56.7047 126.142 55.7912 126.371 54.8838 126.594C54.8502 126.602 54.8168 126.611 54.7832 126.619C54.3532 126.725 53.9242 126.828 53.4971 126.931C53.1867 127.005 52.8771 127.08 52.5684 127.153C51.698 127.36 50.8343 127.563 49.9776 127.76L46.9043 128.45C38.5062 130.294 30.9082 131.622 24.7656 132.5C7.2658 135 -5.73408 132 4.76564 120C14.31 109.092 26.7657 103 36.7656 99C37.4269 98.7355 38.7656 99.4555 37.7656 101C36.8483 102.417 33.7114 104.6 29.2656 108C16.2984 117.916 36.2657 115 47.7656 112.5C59.2656 110 109.766 95 136.266 77C162.766 59 149.766 59.5 146.266 59.5H134.266C133.766 59.4997 132.933 58.2692 135.766 57C140.189 55.0179 150.94 52.3048 165.266 52Z" fill="var(--blue)" />
				<path d="M90.2658 42C117.052 42 138.766 63.7142 138.766 90.5C138.766 91.0386 138.756 91.575 138.738 92.1094C127.033 98.5543 113.467 105.296 99.7658 111.5C85.8954 117.781 70.9287 122.533 57.2326 126.007C47.7188 117.152 41.7658 104.522 41.7658 90.5C41.7658 63.7142 63.48 42 90.2658 42Z" fill="currentColor" fill-opacity="0.7" />
				<circle cx="27.7658" cy="84" r="8" fill="var(--blue)" />
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
			<a
				href={site.appUrl}
				rel="noreferrer"
				aria-label="{site.appName}, the app that implements this format"
				title="The app that implements this format"
				onclick={() => (open = false)}>{site.appName}<span class="ext">↗</span></a
			>
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
	/* The planet mark from the shared favicon, inline so its colours are the
	   page's own and follow data-theme. The full lockups carry gocassini.com's
	   product wordmark, which would read as "GoCassini Format" here; they stay
	   in static/brand/ for surfaces that want the whole thing. */
	.brand__mark {
		display: block;
		flex: none;
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
