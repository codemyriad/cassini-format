<script lang="ts">
	import Doc from '$lib/components/Doc.svelte';
	let { data } = $props();
</script>

<svelte:head>
	<title>Reading a Cassini file — Cassini format</title>
	<meta name="description" content="How to get the transcript out of a Cassini portable meeting file, in shell, JavaScript, Python or Go." />
</svelte:head>

<Doc
	title="Reading a Cassini file"
	kicker="Guide · consumers"
	lede="From a path to a transcript. Eight steps, the same in every language. Every command below was run against the file the front page links to."
	html={data.html}
	headings={data.headings}
/>
