<script lang="ts">
	import Doc from '$lib/components/Doc.svelte';
	let { data } = $props();
</script>

<svelte:head>
	<title>Tools — Cassini format</title>
	<meta
		name="description"
		content="Standalone readers, a producer, the audio digest tool, the conformance suite and a one-line ffprobe recipe for working with Cassini .opus files."
	/>
</svelte:head>

<Doc
	title="Tools"
	kicker="Working with a file"
	lede="Standalone readers and a producer you can copy, the conformance suite that tests an implementation, and one ffprobe line that needs nothing at all."
	html={data.html}
	headings={data.headings}
	wrapTables
	next={[
		{ href: '/consume/', label: 'Read a file in code' },
		{ href: '/produce/', label: 'Create a Cassini file' },
		{ href: '/spec/', label: 'Implement the specification' }
	]}
/>
