<script lang="ts">
	import Doc from '$lib/components/Doc.svelte';
	let { data } = $props();
</script>

<svelte:head>
	<title>Check a Cassini file — what each result establishes</title>
	<meta
		name="description"
		content="Check embedded data, compare the audio with its stored digest, and validate producer output. Understand what a pass, mismatch or unchecked result means."
	/>
</svelte:head>

<Doc
	title="Check a Cassini file."
	kicker="Implementation guide · verification"
	lede="Read the data, check the audio match, and understand the limits of each result. Use the same checks after creating or changing a file."
	html={data.html}
	headings={data.headings}
	wrapTables
	next={[
		{ href: '/build/#check-a-file-then-test-your-implementation', label: 'Test reader behavior' },
		{ href: '/spec/', label: 'Explore the full contract' },
		{ href: '/try/', label: 'Open the result' }
	]}
/>
