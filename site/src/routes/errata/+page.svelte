<script lang="ts">
	import Doc from '$lib/components/Doc.svelte';
	import { site } from '$lib/site';
	let { data } = $props();
</script>

<svelte:head>
	<title>Errata — Cassini format</title>
	<meta
		name="description"
		content="Every place the specification document disagrees with the software, checked against the source and against real files."
	/>
</svelte:head>

<Doc
	title="Where the document and the software disagree"
	kicker="Errata"
	lede="A real file is the tiebreaker. Read this before implementing: several of these otherwise produce a reader that rejects every file written today."
	meta={data.meta}
	html={data.html}
	headings={data.headings}
	source="ERRATA.md"
	sourceHref="{site.repo}/blob/main/ERRATA.md"
/>
