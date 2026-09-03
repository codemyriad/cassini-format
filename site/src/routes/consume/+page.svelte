<script lang="ts">
	import Doc from '$lib/components/Doc.svelte';
	let { data } = $props();
</script>

<svelte:head>
	<title>Reading a Cassini file — Cassini format</title>
	<meta name="description" content="How to read the embedded transcript out of a Cassini .opus audio file, in shell, JavaScript, Python or Go." />
</svelte:head>

<Doc
	title="Reading a Cassini file"
	kicker="Guide · consumers"
	lede="Every command below was run against the file the front page links to."
	html={data.html}
	headings={data.headings}
/>
