<script lang="ts">
	import Doc from '$lib/components/Doc.svelte';
	let { data } = $props();
</script>

<svelte:head>
	<title>Build with Cassini — choose an implementation path</title>
	<meta
		name="description"
		content="Read transcripts, produce portable recordings, or implement Cassini in your own stack. Working guides connect to file checks and conformance tests."
	/>
</svelte:head>

<Doc
	title="Try it in your own tools."
	kicker="Build with Cassini"
	lede="Start with the data you have and the result you need. Reuse the tools, understand the contract, and check your work."
	html={data.html}
	headings={data.headings}
	wrapTables
	next={[
		{ href: '/consume/', label: 'Read a file in code' },
		{ href: '/produce/', label: 'Create a Cassini file' },
		{ href: '/spec/', label: 'Implement the specification' }
	]}
/>
