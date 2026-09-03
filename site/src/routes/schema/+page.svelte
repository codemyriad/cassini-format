<script lang="ts">
	import { base } from '$app/paths';
	let { data } = $props();
</script>

<svelte:head>
	<title>JSON Schemas — Cassini format</title>
	<meta name="description" content="The manifest and transcript-body schemas, CC0, served from a stable URL." />
</svelte:head>

<div class="shell wrap">
	<p class="eyebrow eyebrow--plain">Schemas</p>
	<h1>Machine-readable, CC0, served from here.</h1>
	<p class="lede">
		Every schema in the repository, at a stable path, byte for byte the same file.
	</p>

	<div class="schemas">
		{#each data.schemas as s (s.file)}
			<div class="row">
				<div>
					<p class="t">{s.title}</p>
					<p class="req">requires: {s.required.join(', ') || '—'}</p>
				</div>
				<a class="f" href="{base}/schema/{s.file}">{s.file}</a>
				<span class="b">{(s.bytes / 1024).toFixed(1)} KB</span>
			</div>
		{/each}
	</div>

	<p class="eyebrow">About the <code>$id</code></p>
	<div class="two">
		<div>
			<p>
				Each schema's <code>$id</code> is its URL under
				<code>cassini-format.codemyriad.io/schema/</code>, and this site serves it there. Every
				file carries the same URL in its <code>CASSINI_PAYLOAD_SCHEMA</code> tag, so a reader
				holding only the file can find the schema it claims to follow.
			</p>
		</div>
		<div class="code">
			<div class="code__bar"><span>json</span></div>
			{@html data.headHtml}
		</div>
	</div>
</div>

<style>
	.wrap {
		padding-top: 3.5rem;
	}
	h1 {
		margin: 1.1rem 0 1.2rem;
		max-width: 26ch;
	}
	.eyebrow {
		margin: 4rem 0 1.4rem;
	}
	.schemas {
		display: grid;
		border: 1px solid var(--rule);
		background: var(--rule);
		gap: 1px;
		margin-top: 2rem;
	}
	.row {
		display: grid;
		grid-template-columns: minmax(0, 1fr) minmax(0, 24rem) auto;
		gap: 1.5rem;
		background: var(--bg);
		padding: 0.9rem 1rem;
		align-items: baseline;
		font-size: 12.5px;
	}
	@media (max-width: 860px) {
		.row {
			grid-template-columns: minmax(0, 1fr);
			gap: 0.3rem;
		}
	}
	.t {
		margin: 0;
		color: var(--fg);
	}
	.req {
		margin: 0.2rem 0 0;
		color: var(--fg-5);
		font-size: 11.5px;
	}
	.f {
		word-break: break-all;
	}
	.b {
		color: var(--fg-5);
	}
	.two {
		display: grid;
		grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
		gap: 2rem;
		align-items: start;
	}
	@media (max-width: 950px) {
		.two {
			grid-template-columns: minmax(0, 1fr);
		}
	}
</style>
