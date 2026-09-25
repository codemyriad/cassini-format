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
	title="Read a file in code"
	kicker="Implementation guide · reading"
	lede="Bring words, timestamps and speakers into your application. Start with a working reader, then understand and check the result."
	html={data.html}
	headings={data.headings}
	next={[
		{ href: '/spec/v1/#trust-and-integrity', label: 'What each read state means' },
		{ href: '/build/#check-a-file-then-test-your-implementation', label: 'Test your reader' },
		{ href: '/produce/', label: 'Create a file' }
	]}
/>
