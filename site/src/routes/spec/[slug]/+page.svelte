<script lang="ts">
	import { base } from '$app/paths';
	import Doc from '$lib/components/Doc.svelte';
	import { versions } from '$lib/site';

	let { data } = $props();
	const isVersion = $derived(/^v\d+$/.test(data.slug));
</script>

<svelte:head>
	<title>{data.title} — Cassini format</title>
	<meta name="description" content={data.lede} />
</svelte:head>

<Doc
	title={data.title}
	kicker={data.kicker}
	lede={data.lede}
	meta={data.meta}
	html={data.html}
	headings={data.headings}
	source={data.source}
	sourceHref={data.sourceHref}
>
	{#snippet banner()}
		{#if isVersion}
			<div class="rail">
				{#each versions as v (v.slug)}
					<a href="{base}/spec/{v.slug}/" class:on={data.slug === v.slug}>
						{v.label}<span>{v.status}</span>
					</a>
				{/each}
				<a href="{base}/spec/document/" class:on={data.slug === 'document'}>
					full document<span>all versions</span>
				</a>
			</div>
		{/if}
	{/snippet}
</Doc>

<style>
	.rail {
		display: flex;
		flex-wrap: wrap;
		gap: 1px;
		margin-top: 1.5rem;
		background: var(--rule);
		border: 1px solid var(--rule);
		width: fit-content;
	}
	.rail a {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
		background: var(--bg);
		color: var(--fg-3);
		padding: 0.5rem 0.9rem;
		font-size: 13px;
	}
	.rail a span {
		font-size: 10.5px;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--fg-5);
	}
	.rail a:hover {
		color: var(--fg);
		text-decoration: none;
		background: var(--bg-raise);
	}
	.rail a.on {
		color: var(--blue);
		background: var(--blue-wash);
	}
	.rail a.on span {
		color: var(--blue-dim);
	}
</style>
