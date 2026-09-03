<script lang="ts">
	import type { Heading } from '$lib/markdown';

	let {
		title,
		kicker = '',
		lede = '',
		html,
		headings = [],
		source = '',
		sourceHref = '',
		meta = [],
		banner
	}: {
		title: string;
		kicker?: string;
		lede?: string;
		html: string;
		headings?: Heading[];
		source?: string;
		sourceHref?: string;
		meta?: { label: string; value: string }[];
		banner?: import('svelte').Snippet;
	} = $props();

	let active = $state('');

	$effect(() => {
		const targets = headings
			.map((h) => document.getElementById(h.id))
			.filter((el): el is HTMLElement => !!el);
		if (!targets.length) return;
		const io = new IntersectionObserver(
			(entries) => {
				const visible = entries.filter((e) => e.isIntersecting);
				if (visible.length) active = visible[0].target.id;
			},
			{ rootMargin: '-70px 0px -70% 0px' }
		);
		targets.forEach((t) => io.observe(t));
		return () => io.disconnect();
	});
</script>

<div class="shell doc" class:doc--wide={headings.length <= 2}>
	<article>
		<header>
			{#if kicker}<p class="eyebrow eyebrow--plain">{kicker}</p>{/if}
			<h1>{title}</h1>
			{#if lede}<p class="lede">{lede}</p>{/if}
			{#if meta.length}
				<dl class="meta">
					{#each meta as m (m.label)}
						<div><dt>{m.label}</dt><dd>{m.value}</dd></div>
					{/each}
				</dl>
			{/if}
			{#if banner}{@render banner()}{/if}
		</header>

		<div class="prose">{@html html}</div>

		{#if source}
			<p class="src">
				Rendered from <a href={sourceHref} rel="noreferrer"><code>{source}</code></a> in the
				repository.
			</p>
		{/if}
	</article>

	{#if headings.length > 2}
		<aside>
			<nav aria-label="On this page">
				<p class="eyebrow eyebrow--plain">On this page</p>
				<ul>
					{#each headings as h (h.id)}
						<li data-depth={h.depth} class:on={active === h.id}>
							<a href="#{h.id}">{h.text}</a>
						</li>
					{/each}
				</ul>
			</nav>
		</aside>
	{/if}
</div>

<style>
	.doc {
		display: grid;
		grid-template-columns: minmax(0, 1fr) 15rem;
		gap: 3.5rem;
		padding-top: 3.5rem;
		align-items: start;
	}
	/* No table of contents means no empty right-hand column. */
	.doc--wide {
		grid-template-columns: minmax(0, 1fr);
	}
	@media (max-width: 1050px) {
		.doc {
			grid-template-columns: minmax(0, 1fr);
			gap: 0;
		}
		aside {
			display: none;
		}
	}
	article {
		min-width: 0;
		max-width: 82ch;
	}
	header {
		border-bottom: 1px solid var(--rule);
		padding-bottom: 1.75rem;
		margin-bottom: 2.25rem;
	}
	header h1 {
		margin: 1.1rem 0 0;
	}
	header .lede {
		margin: 1rem 0 0;
		color: var(--fg-3);
	}
	.meta {
		display: flex;
		flex-wrap: wrap;
		gap: 0 2rem;
		margin: 1.4rem 0 0;
		font-size: 12px;
	}
	.meta div {
		display: flex;
		gap: 0.5rem;
	}
	dt {
		color: var(--fg-5);
		text-transform: uppercase;
		letter-spacing: 0.1em;
		font-size: 11px;
		line-height: 1.7;
	}
	dd {
		margin: 0;
		color: var(--fg-2);
	}

	.src {
		margin-top: 4rem;
		padding-top: 1.25rem;
		border-top: 1px solid var(--rule);
		color: var(--fg-4);
		font-size: 12.5px;
	}

	aside {
		position: sticky;
		top: 5rem;
		max-height: calc(100vh - 7rem);
		overflow-y: auto;
		font-size: 12.5px;
	}
	aside ul {
		list-style: none;
		margin: 0.9rem 0 0;
		padding: 0;
		display: grid;
		gap: 0.15rem;
		border-left: 1px solid var(--rule);
	}
	aside li a {
		display: block;
		color: var(--fg-4);
		padding: 0.12rem 0 0.12rem 0.85rem;
		margin-left: -1px;
		border-left: 1px solid transparent;
		line-height: 1.45;
	}
	aside li[data-depth='3'] a {
		padding-left: 1.7rem;
		font-size: 12px;
	}
	aside li[data-depth='4'] a {
		padding-left: 2.5rem;
		font-size: 12px;
	}
	aside li a:hover {
		color: var(--fg-2);
		text-decoration: none;
	}
	aside li.on a {
		color: var(--blue);
		border-left-color: var(--blue);
	}

	/* ---- prose ---- */
	.prose :global(h1) {
		margin: 4rem 0 1.2rem;
		padding-top: 1.6rem;
		border-top: 1px solid var(--rule-hi);
		font-size: clamp(1.4rem, 1.15rem + 1.1vw, 1.85rem);
	}
	.prose :global(h1:first-child) {
		margin-top: 0;
		padding-top: 0;
		border-top: 0;
	}
	.prose :global(h2) {
		margin: 3rem 0 1rem;
		padding-top: 1.4rem;
		border-top: 1px solid var(--rule);
	}
	.prose :global(h3) {
		margin: 2.1rem 0 0.7rem;
	}
	.prose :global(h4) {
		margin: 1.6rem 0 0.5rem;
		color: var(--fg-2);
	}
	.prose :global(:is(h1, h2, h3, h4) > .anchor) {
		color: var(--fg-5);
		margin-left: 0.6rem;
		font-weight: 400;
		opacity: 0;
		text-decoration: none;
	}
	.prose :global(:is(h1, h2, h3, h4):hover > .anchor) {
		opacity: 1;
	}
	.prose :global(ul),
	.prose :global(ol) {
		max-width: var(--col);
		padding-left: 1.3rem;
		margin: 0 0 1.05em;
	}
	.prose :global(li) {
		margin-bottom: 0.35em;
	}
	.prose :global(li::marker) {
		color: var(--fg-5);
	}
	.prose :global(.code) {
		margin: 1.4rem 0;
	}
	.prose :global(blockquote) {
		margin: 1.4rem 0;
		padding: 0.1rem 0 0.1rem 1.1rem;
		border-left: 2px solid var(--rule-hi);
		color: var(--fg-3);
	}
	.prose :global(table) {
		width: 100%;
		border-collapse: collapse;
		margin: 1.5rem 0;
		font-size: 12.5px;
		display: block;
		overflow-x: auto;
	}
	.prose :global(th) {
		text-align: left;
		font-weight: 500;
		color: var(--fg-4);
		text-transform: uppercase;
		letter-spacing: 0.08em;
		font-size: 11px;
		padding: 0.5rem 0.9rem 0.5rem 0;
		border-bottom: 1px solid var(--rule-hi);
		white-space: nowrap;
	}
	.prose :global(td) {
		padding: 0.5rem 0.9rem 0.5rem 0;
		border-bottom: 1px solid var(--rule);
		color: var(--fg-2);
		vertical-align: top;
	}
	.prose :global(td:first-child) {
		white-space: nowrap;
	}
	.prose :global(hr) {
		margin: 3rem 0;
	}
	.prose :global(img) {
		max-width: 100%;
	}
	.prose :global(strong) {
		color: var(--fg);
		font-weight: 600;
	}
</style>
