<script lang="ts">
	import Doc from '$lib/components/Doc.svelte';
	let { data } = $props();
</script>

<svelte:head>
	<title>Writing a Cassini file — Cassini format</title>
	<meta
		name="description"
		content="How to embed a word-timed transcript in an Ogg Opus audio file: the requirements for a valid Cassini file, with a complete producer in stdlib Python."
	/>
</svelte:head>

<Doc
	title="Write a Cassini file"
	kicker="Implementation guide · writing"
	lede="Pack an Opus recording and a word-timed transcript into one file. Start with the Python producer, then explore the format requirements."
	html={data.html}
	headings={data.headings}
/>
