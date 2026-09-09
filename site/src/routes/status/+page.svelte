<script lang="ts">
	import Doc from '$lib/components/Doc.svelte';
	let { data } = $props();
</script>

<svelte:head>
	<title>Status — Cassini format</title>
	<meta
		name="description"
		content="Where the format comes from, who uses it, what is stable and what the software still owes the spec."
	/>
</svelte:head>

<Doc
	title="Project status"
	kicker="The project · version 1"
	lede="Where Cassini is used, what is stable, and what implementers need to know about compatibility."
	html={data.html}
	headings={data.headings}
/>
