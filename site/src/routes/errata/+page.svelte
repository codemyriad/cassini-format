<script lang="ts">
	import Doc from '$lib/components/Doc.svelte';
	import { site } from '$lib/site';
	let { data } = $props();
</script>

<svelte:head>
	<title>Errata — Cassini format</title>
	<meta
		name="description"
		content="Where the reference implementations still lag the specification, checked against the source and against real files."
	/>
</svelte:head>

<Doc
	title="Where the document and the software disagree"
	kicker="Errata"
	lede="The specification is the rule. This is where the reference implementations still lag it, and a few facts about real files worth knowing before you write a reader."
	meta={data.meta}
	html={data.html}
	headings={data.headings}
	source="ERRATA.md"
	sourceHref="{site.repo}/blob/main/ERRATA.md"
/>
