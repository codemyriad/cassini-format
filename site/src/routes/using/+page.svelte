<script lang="ts">
	import Doc from '$lib/components/Doc.svelte';
	let { data } = $props();
</script>

<svelte:head>
	<title>Using Cassini — from a recording to a portable file</title>
	<meta
		name="description"
		content="Keep the recording with its transcript so you can listen and check what was said. Learn how to create, share and open a Cassini file, and where the format fits."
	/>
</svelte:head>

<Doc
	title="A small format from our own meetings."
	kicker="Using Cassini"
	lede="Use the transcript to find a passage and the recording to check what was said. Here is how to create, share and open that file."
	html={data.html}
	headings={data.headings}
	wrapTables
/>
