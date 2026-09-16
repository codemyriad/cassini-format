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
	title="Create a Cassini file"
	kicker="Implementation guide · writing"
	lede="Take existing audio and timed words through packaging, checking and sharing. Try the complete example, then use your own inputs."
	html={data.html}
	headings={data.headings}
	next={[
		{ href: '/build/#check-a-file-then-test-your-implementation', label: 'Run the conformance suite' },
		{ href: '/try/', label: 'Open and listen' },
		{ href: '/spec/', label: 'Implement your own producer' }
	]}
/>
