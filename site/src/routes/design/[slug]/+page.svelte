<script lang="ts">
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
/>
