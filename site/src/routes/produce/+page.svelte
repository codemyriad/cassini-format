<script lang="ts">
	import Doc from '$lib/components/Doc.svelte';
	let { data } = $props();
</script>

<svelte:head>
	<title>Writing a Cassini file — Cassini format</title>
	<meta name="description" content="What a producer must write to make a valid Cassini portable meeting file, with a complete reference producer in stdlib Python." />
</svelte:head>

<Doc
	title="Writing a Cassini file"
	kicker="Guide · producers"
	lede="What a producer has to get right, as requirements you can check off, then the conventions that are merely a good idea."
	html={data.html}
	headings={data.headings}
/>
