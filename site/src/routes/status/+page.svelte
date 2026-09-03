<script lang="ts">
	import Doc from '$lib/components/Doc.svelte';
	let { data } = $props();
</script>

<svelte:head>
	<title>Status — Cassini format</title>
	<meta name="description" content="Where the format comes from, who uses it, what is stable and what the software still owes the spec." />
</svelte:head>

<Doc
	title="Status"
	kicker="Status · 2026-09-02"
	html={data.html}
	headings={data.headings}
/>
