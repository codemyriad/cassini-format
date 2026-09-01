<script lang="ts">
	import Doc from '$lib/components/Doc.svelte';
	let { data } = $props();
</script>

<svelte:head>
	<title>Status — Cassini format</title>
	<meta name="description" content="What is stable in the format, what is still moving, and what is not written down yet." />
</svelte:head>

<Doc
	title="Where the format actually stands"
	kicker="Status · 2026-09-01"
	lede="Shipped and load-bearing, with a short list of things I would fix before calling it frozen."
	html={data.html}
	headings={data.headings}
/>
