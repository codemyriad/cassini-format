<script lang="ts">
	import { base } from '$app/paths';
	let { data } = $props();
</script>

<svelte:head>
	<title>Design notes — Cassini format</title>
	<meta name="description" content="The measurements and arguments behind the parts of the spec that are not obvious." />
</svelte:head>

<div class="shell wrap">
	<p class="eyebrow eyebrow--plain">Design notes</p>
	<h1>Why the format is shaped this way.</h1>
	<p class="lede">
		The measurements and arguments behind the parts of the spec that are not obvious. Not
		normative: where a note and the spec disagree, the spec wins.
	</p>

	<ol class="list">
		{#each data.docs as doc, i (doc.slug)}
			<li>
				<a href="{base}/design/{doc.slug}/">
					<span class="n">{String(i + 1).padStart(2, '0')}</span>
					<span class="body">
						<span class="t">{doc.title}</span>
						<span class="blurb">{doc.blurb}…</span>
					</span>
					{#if doc.date}<span class="d">{doc.date}</span>{/if}
				</a>
			</li>
		{/each}
	</ol>
</div>

<style>
	.wrap {
		padding-top: 3.5rem;
	}
	h1 {
		margin: 1.1rem 0 1.2rem;
		max-width: 24ch;
	}
	.list {
		list-style: none;
		margin: 2.5rem 0 0;
		padding: 0;
		border-top: 1px solid var(--rule);
	}
	.list li {
		border-bottom: 1px solid var(--rule);
	}
	.list a {
		display: grid;
		grid-template-columns: 3rem minmax(0, 1fr) auto;
		gap: 1.5rem;
		padding: 1.15rem 0.75rem;
		color: inherit;
		align-items: baseline;
	}
	.list a:hover {
		background: var(--bg-raise);
		text-decoration: none;
	}
	.n {
		color: var(--fg-5);
		font-size: 11px;
		letter-spacing: 0.12em;
	}
	.body {
		display: grid;
		gap: 0.35rem;
		min-width: 0;
		overflow-wrap: anywhere;
	}
	.t {
		color: var(--fg);
		font-size: 15px;
		font-weight: 500;
	}
	.list a:hover .t {
		color: var(--blue);
	}
	.blurb {
		color: var(--fg-4);
		font-size: 12.5px;
		line-height: 1.55;
		max-width: 76ch;
	}
	.d {
		color: var(--fg-5);
		font-size: 11.5px;
		white-space: nowrap;
	}
	@media (max-width: 760px) {
		.list a {
			grid-template-columns: 2.2rem minmax(0, 1fr);
		}
		.d {
			display: none;
		}
	}
</style>
