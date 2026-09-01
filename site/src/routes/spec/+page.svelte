<script lang="ts">
	import { base } from '$app/paths';
	import { site } from '$lib/site';
	let { data } = $props();
</script>

<svelte:head>
	<title>Specification — Cassini format</title>
	<meta name="description" content="Every version of the Cassini portable meeting format, with a permanent URL each." />
</svelte:head>

<div class="shell wrap">
	<p class="eyebrow eyebrow--plain">Specification</p>
	<h1>One published version.</h1>
	<p class="lede">
		Two shapes came before this one. Both were used only inside Cassini and neither was ever
		published, so this is the first version anyone outside can implement.
	</p>

	<div class="grid vers">
		<a class="v v--now" href="{base}/spec/v1/">
			<p class="tag">current</p>
			<h2>v3</h2>
			<p class="wire">org.cassini.portable-meeting/1</p>
			<p>
				Identity moved from decoded PCM to the compressed Opus packets. The old digest depended on
				which decoder you linked, and so did a meeting's id.
			</p>
		</a>
	</div>

	<p class="also">
		Or <a href="{base}/spec/document/">the whole document on one page</a>, rationale and rejected
		alternatives included.
	</p>

	<p class="eyebrow">The pieces a version points at</p>
	<div class="grid grid--2">
		<a class="v" href="{base}/spec/words-v1/">
			<h3>cassini.words.v1</h3>
			<p>
				One item per word, with a speaker and a start and end in milliseconds. A v1 file inlines it,
				a v3 file gives it its own chunk set. One document type, one schema.
			</p>
		</a>
		<a class="v" href="{base}/spec/audio-integrity/">
			<h3>exact-opus-audio-v1</h3>
			<p>
				The audio digest, byte by byte. It covers the Opus packets and excludes OpusTags, so writing
				the digest into the file cannot change it.
			</p>
		</a>
	</div>

	<p class="eyebrow">Schemas</p>
	<p class="lede">CC0, served from this site at a stable URL. Copy them into your project.</p>
	<div class="schemas">
		{#each data.schemas as s (s.file)}
			<a href="{base}/schema/{s.file}">
				<span class="f">{s.file}</span>
				<span class="t">{s.title}</span>
				<span class="b">{(s.bytes / 1024).toFixed(1)} KB</span>
			</a>
		{/each}
	</div>
	<p class="also">
		<a href="{base}/schema/">Why the <code>$id</code> in those files does not resolve yet</a>.
	</p>

	<p class="eyebrow">Licence</p>
	<p class="lede">
		Prose CC BY 4.0; schemas, test vectors and example code CC0. The reference implementation stays
		AGPL-3.0, deliberately a separate question: you can implement this without touching
		<a href={site.implRepo} rel="noreferrer">gocassini</a> at all.
	</p>
</div>

<style>
	.wrap {
		padding-top: 3.5rem;
	}
	h1 {
		margin: 1.1rem 0 1.2rem;
		max-width: 24ch;
	}
	.eyebrow {
		margin: 4rem 0 1.4rem;
	}
	.vers {
		margin: 2.2rem 0 1rem;
	}
	.v {
		display: block;
		color: inherit;
	}
	.v:hover {
		background: var(--bg-raise) !important;
		text-decoration: none;
	}
	.v h2 {
		margin: 0.5rem 0 0.35rem;
		font-size: 1.5rem;
	}
	.v h3 {
		margin: 0 0 0.5rem;
		color: var(--blue);
	}
	.v p {
		font-size: 13px;
		color: var(--fg-3);
		margin: 0;
		max-width: none;
	}
	.v p + p {
		margin-top: 0.6rem;
	}
	.tag {
		font-size: 10.5px !important;
		letter-spacing: 0.12em;
		text-transform: uppercase;
		color: var(--fg-5) !important;
	}
	.v--now .tag {
		color: var(--blue) !important;
	}
	.v--now h2 {
		color: var(--blue);
	}
	.wire {
		color: var(--fg-4) !important;
		font-size: 11.5px !important;
		word-break: break-all;
	}
	.also {
		margin-top: 1.2rem;
		font-size: 13px;
		color: var(--fg-4);
	}
	.schemas {
		display: grid;
		border: 1px solid var(--rule);
		background: var(--rule);
		gap: 1px;
		margin-top: 1.5rem;
	}
	.schemas a {
		display: grid;
		grid-template-columns: minmax(0, 22rem) minmax(0, 1fr) auto;
		gap: 1rem;
		background: var(--bg);
		padding: 0.7rem 1rem;
		color: var(--fg-3);
		font-size: 12.5px;
		align-items: baseline;
	}
	.schemas a:hover {
		background: var(--bg-raise);
		text-decoration: none;
		color: var(--fg);
	}
	.schemas .f {
		color: var(--blue);
		word-break: break-all;
	}
	.schemas .b {
		color: var(--fg-5);
	}
	@media (max-width: 760px) {
		.schemas a {
			grid-template-columns: minmax(0, 1fr);
			gap: 0.2rem;
		}
	}
</style>
