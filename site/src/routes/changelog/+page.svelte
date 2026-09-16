<script lang="ts">
	import Doc from '$lib/components/Doc.svelte';
	let { data } = $props();
</script>

<svelte:head>
	<title>Changelog — Cassini format</title>
	<meta
		name="description"
		content="Versions of the Cassini portable meeting format: version 1, the private drafts before it, and the specification changes since."
	/>
</svelte:head>

<Doc
	title="Changelog"
	kicker="Versions of the format"
	html={data.html}
	headings={data.headings}
	source={data.source}
	sourceHref={data.sourceHref}
	next={[
		{ href: '/spec/v1/', label: 'The current specification' },
		{ href: '/design/', label: 'Design notes' }
	]}
/>
