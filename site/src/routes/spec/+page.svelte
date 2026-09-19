<script lang="ts">
	import { base } from '$app/paths';
	import { site } from '$lib/site';
	let { data } = $props();
</script>

<svelte:head>
	<title>Specification & implementation resources — Cassini</title>
	<meta
		name="description"
		content="The Cassini v1 specification, transcript format, audio digest, JSON Schemas and conformance suite. Everything you need to implement the open format."
	/>
</svelte:head>

<div class="shell page-intro">
	<h1>Specification</h1>
</div>

<div class="shell reference">
	<a class="current" href="{base}/spec/v1/">
		<p class="eyebrow eyebrow--plain">Current version · Published 2 September 2026</p>
		<h2>Cassini v1 <span aria-hidden="true">→</span></h2>
		<p class="current-what">
			The file structure, metadata, producer requirements and reader behavior.
		</p>
	</a>

	<section aria-labelledby="versions">
		<h2 id="versions">Versions</h2>
		<ul class="versions">
			<li>
				<a href="{base}/spec/v1/"><strong>v1</strong></a>
				<span>Current · published 2026-09-02</span><code>org.cassini.portable-meeting/1</code>
			</li>
			<li>
				<a href="{base}/changelog/#private-draft-3--orgcassiniportable-meeting1-2026-08-29"
					><strong>Private draft 3</strong></a
				>
				<span>History · 2026-08-29</span><code>org.cassini.portable-meeting/1</code>
			</li>
			<li>
				<a href="{base}/changelog/#private-draft-2--orgcassiniportable-meeting2-2026-05-12"
					><strong>Private draft 2</strong></a
				>
				<span>History · 2026-05-12</span><code>org.cassini.portable-meeting/2</code>
			</li>
			<li>
				<a href="{base}/changelog/#private-draft-1--orgcassiniportable-meeting1-2026-03"
					><strong>Private draft 1</strong></a
				>
				<span>History · 2026-03</span><code>org.cassini.portable-meeting/1</code>
			</li>
		</ul>
		<p class="versions-more">
			<a href="{base}/changelog/">Every change to the specification →</a>
		</p>
	</section>

	<section aria-labelledby="contracts">
		<h2 id="contracts">Supporting contracts</h2>
		<div class="resources">
			<a href="{base}/spec/words-v1/"
				><div>
					<h3>Transcript body</h3>
					<p>A word, its speaker, and start and end times in milliseconds.</p>
					<code>cassini.words.v1</code>
				</div>
				<span aria-hidden="true">↗</span></a
			>
			<a href="{base}/spec/audio-integrity/"
				><div>
					<h3>Audio digest</h3>
					<p>The exact bytes used to match a transcript to a recording, independent of its tags.</p>
					<code>exact-opus-audio-v1</code>
				</div>
				<span aria-hidden="true">↗</span></a
			>
		</div>
	</section>

	<section aria-labelledby="validation">
		<h2 id="validation">Validate your implementation</h2>
		<div class="schema-list">
			{#each data.schemas as schema (schema.file)}<a href="{base}/schema/{schema.file}"
					><span><strong>{schema.title}</strong><small>{schema.file}</small></span><span
						class="schema-size">{(schema.bytes / 1024).toFixed(1)} KB ↗</span
					></a
				>{/each}
		</div>
		<div class="resource-links">
			<a href="{base}/produce/#checking-your-work">Check a produced file →</a>
			<a href="{base}/build/#check-a-file-then-test-your-implementation">Run reader conformance checks →</a>
			<a href="{base}/schema/">About the schemas →</a><a
				href="{site.repo}/tree/main/spec/conformance">Conformance suite on GitHub ↗</a
			><a href="{base}/demo/cassini-final-moments.opus" download>Download an example file ↓</a>
		</div>
	</section>

	<section class="further" aria-labelledby="further">
		<h2 id="further">Further reading</h2>
		<nav aria-label="Related resources">
			<a href="{base}/consume/"
				>Read a file <span>Python, JavaScript and the decoding algorithm →</span></a
			><a href="{base}/produce/"
				>Write a file <span>A complete producer and validation steps →</span></a
			><a href="{base}/design/">Design notes <span>Tradeoffs, measurements and rationale →</span></a
			><a href="{base}/llms-full.txt"
				>The complete specification as text <span>One file for tools and coding assistants ↗</span
				></a
			>
		</nav>
	</section>

	<p class="licence">
		Specification text: CC BY 4.0. Schemas, test vectors and standalone readers/producer: CC0. The <a
			href={site.implRepo}>gocassini reference application</a
		> and the site's Cassini transcript component are AGPL-3.0.
	</p>
</div>

<style>
	.reference section {
		margin-top: 2.75rem;
	}
	.reference section > h2 {
		font-size: 25px;
		margin-bottom: 1rem;
	}
	/* Same compact card as the home page's specification section. */
	.current {
		display: grid;
		grid-template-columns: minmax(0, 1fr) auto;
		grid-template-areas: 'meta title' 'what title';
		align-items: center;
		gap: 0.4rem 1.5rem;
		padding: 1.25rem 1.75rem;
		border: 1px solid var(--blue-rule);
		border-radius: 7px;
		background: var(--blue-wash);
		color: inherit;
	}
	.current:hover {
		text-decoration: none;
		border-color: var(--blue);
	}
	.current .eyebrow {
		grid-area: meta;
		margin: 0;
		color: var(--blue);
		line-height: 1.6;
	}
	.current h2 {
		grid-area: title;
		margin: 0;
		font-size: 25px;
		white-space: nowrap;
	}
	.current h2 span {
		color: var(--blue);
		margin-left: 0.5rem;
	}
	.current-what {
		grid-area: what;
		margin: 0;
		font-size: 15px;
	}
	.resources {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1.5rem;
	}
	.resources > a {
		display: flex;
		gap: 1rem;
		align-items: baseline;
		padding: 1.25rem;
		border: 1px solid var(--rule);
		border-radius: 6px;
		color: inherit;
	}
	.resources > a:hover {
		background: var(--bg-raise);
		text-decoration: none;
	}
	.resources > a > span:last-child {
		margin-left: auto;
		color: var(--blue);
	}
	.resources h3 {
		margin-bottom: 0.4rem;
	}
	.resources p {
		font-size: 15px;
	}
	.resources code {
		font-size: 11px;
	}
	.schema-list {
		border-top: 1px solid var(--rule);
	}
	.schema-list a {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
		padding-block: 0.8rem;
		border-bottom: 1px solid var(--rule);
	}
	.schema-list a strong {
		font-size: 16px;
		font-weight: 500;
	}
	.schema-list a small {
		display: block;
		font: 11px var(--mono);
		color: var(--fg-4);
		margin-top: 0.3rem;
		overflow-wrap: anywhere;
	}
	.schema-size {
		font: 11px var(--mono);
		white-space: nowrap;
		color: var(--fg-4);
	}
	.resource-links {
		display: flex;
		flex-wrap: wrap;
		gap: 0.75rem 2rem;
		font-size: 14px;
		margin-top: 1rem;
	}
	.further nav {
		display: grid;
		border-top: 1px solid var(--rule);
	}
	.further nav a {
		border-bottom: 1px solid var(--rule);
		padding: 0.8rem 0;
		font-size: 16px;
	}
	.further nav span {
		display: block;
		font-size: 13px;
		color: var(--fg-4);
		margin-top: 0.25rem;
	}
	.versions {
		list-style: none;
		margin: 0;
		padding: 0;
		border-top: 1px solid var(--rule);
	}
	.versions li {
		display: flex;
		flex-wrap: wrap;
		align-items: baseline;
		gap: 0.4rem 1.5rem;
		padding-block: 0.7rem;
		border-bottom: 1px solid var(--rule);
		font-size: 15px;
	}
	.versions li > span {
		color: var(--fg-4);
		font-size: 13px;
	}
	.versions code {
		margin-left: auto;
		font-size: 11px;
	}
	.versions-more {
		margin-top: 1rem;
		font-size: 14px;
	}
	.licence {
		margin-top: 3rem;
		font-size: 13px;
		color: var(--fg-4);
	}
	@media (max-width: 720px) {
		.resources {
			grid-template-columns: minmax(0, 1fr);
		}
		.current {
			grid-template-areas: 'meta' 'title' 'what';
			grid-template-columns: minmax(0, 1fr);
			padding: 1.25rem;
		}
	}
</style>
