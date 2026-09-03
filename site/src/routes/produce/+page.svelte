<script lang="ts">
	import Doc from '$lib/components/Doc.svelte';
	let { data } = $props();
</script>

<svelte:head>
	<title>Writing a Cassini file — Cassini format</title>
	<meta name="description" content="How to embed a word-timed transcript in an Ogg Opus audio file: the requirements for a valid Cassini file, with a complete producer in stdlib Python." />
</svelte:head>

<Doc
	title="Writing a Cassini file"
	kicker="Guide · producers"
	lede="The requirements, then the conventions."
	html={data.html}
	headings={data.headings}
/>
