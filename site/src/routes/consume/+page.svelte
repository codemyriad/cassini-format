<script lang="ts">
	import Doc from '$lib/components/Doc.svelte';
	let { data } = $props();
</script>

<svelte:head>
	<title>Reading a Cassini file — Cassini format</title>
	<meta
		name="description"
		content="How to read the embedded transcript out of a Cassini .opus audio file, in shell, JavaScript, Python or Go."
	/>
</svelte:head>

<Doc
	title="Read a Cassini file"
	kicker="Implementation guide · reading"
	lede="Extract the words, preserve the speakers, and handle every reader state. Start with a working example in Python or JavaScript."
	html={data.html}
	headings={data.headings}
/>
