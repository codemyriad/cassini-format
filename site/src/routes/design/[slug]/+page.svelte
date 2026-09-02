<script lang="ts">
	import { base } from '$app/paths';
	import Doc from '$lib/components/Doc.svelte';
	let { data } = $props();
</script>

<svelte:head>
	<title>{data.title} — Cassini format</title>
</svelte:head>

<Doc
	title={data.title}
	kicker="Design note"
	meta={data.date ? [{ label: 'Written', value: data.date }] : []}
	html={data.html}
	headings={data.headings}
	source={data.source}
	sourceHref={data.sourceHref}
>
	{#snippet banner()}
		<p class="hist">
			A working document, kept as written. It is not the specification: where it and
			<a href="{base}/spec/v1/">the spec</a> disagree, the spec wins.
		</p>
	{/snippet}
</Doc>

<style>
	.hist {
		margin: 1.5rem 0 0;
		padding: 0.6rem 0.9rem;
		border-left: 2px solid var(--amber-rule);
		color: var(--fg-4);
		font-size: 12.5px;
		max-width: 68ch;
	}
</style>
