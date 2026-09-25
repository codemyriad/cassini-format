<script lang="ts">
	import { base } from '$app/paths';
	import { site } from '$lib/site';
	import TagDump from '$lib/components/TagDump.svelte';
	import Player from '$lib/components/Player.svelte';

	let { data } = $props();
	const mb = (n: number) => `${(n / 1024 / 1024).toFixed(2)} MB`;
	const minutes = (ms: number) =>
		`${Math.floor(ms / 60000)}:${String(Math.floor((ms % 60000) / 1000)).padStart(2, '0')}`;

	/** The static schematic that used to sit behind the "Audio" layer button. */
	const tree = 'meeting.opus\n├── OpusHead\n├── OpusTags\n└── audio';

	const tools = [
		{
			name: 'Browser reader',
			what: 'Opens a file and plays it with its transcript, without installing anything',
			href: `${base}/try/`,
			meta: 'In your browser'
		},
		{
			name: 'Python readers',
			what: 'Parse the Ogg container directly, or print the tags, the manifest or one transcript with ffprobe',
			href: `${base}/build/`,
			meta: 'Python, CC0'
		},
		{
			name: 'Python producer',
			what: 'Packs Ogg Opus audio and timed words into a Cassini file',
			href: `${site.repo}/blob/main/tools/cassini-pack.py`,
			meta: 'Python, stdlib only'
		},
		{
			name: 'JavaScript reader',
			what: 'Reads a file in the browser: fetch, DecompressionStream, crypto.subtle',
			href: `${site.repo}/blob/main/tools/cassini-read.js`,
			meta: 'No dependencies, CC0'
		},
		{
			name: 'ffprobe one-liner',
			what: 'Dumps the payload with no script and no library',
			href: `${base}/consume/#the-payload-in-one-pipeline`,
			meta: 'Shell'
		},
		{
			name: 'Conformance suite',
			what: 'Test vectors and an adapter protocol for testing a reader in any language',
			href: `${base}/build/#check-a-file-then-test-your-implementation`,
			meta: 'Python harness, CC0'
		}
	];
</script>

<svelte:head>
	<title>Cassini — a whole meeting in one file</title>
	<meta name="description" content={site.description} />
</svelte:head>

<section class="hero shell" aria-labelledby="hero-title">
	<h1 id="hero-title">
		A whole meeting<br /><span>in one file.</span>
	</h1>
	<p class="hero-lede">
		A Cassini portable meeting file is an ordinary Ogg <code>.opus</code> audio file at 48 kHz.
	</p>
	<p class="hero-description">
		What makes it special is everything packed in alongside the audio: the transcript, the speakers,
		a summary if you asked for one, and a record of what produced them, all written into the file's
		own tags, right next to <code>TITLE</code> and <code>DATE</code>. No sidecar to lose.
	</p>
	<a class="release" href="{base}/changelog/"
		><span class="release-dot"></span> v{site.currentVersion}
		<span class="release-divider">·</span>
		<code>{site.formatId}</code>
		<span class="release-divider">·</span>
		last change {data.change.date} <span aria-hidden="true">→</span></a
	>
	<div class="actions">
		<a class="button button--primary" href="{base}/spec/v1/"
			>Read the spec <span aria-hidden="true">→</span></a
		>
		<a class="button" href="{base}/build/">Build with it</a>
	</div>
</section>

<section class="shell section" id="example" aria-labelledby="example-title">
	<div class="section-heading">
		<h2 id="example-title">An example file</h2>
	</div>

	<div class="proof">
		<div class="example">
			<div class="example-top">
				<span class="eyebrow eyebrow--plain">Listen &amp; follow along</span><span class="file-type"
					>.opus</span
				>
			</div>
			<div class="example-heading">
				<h3>{data.demo.title}</h3>
				<p>
					{data.demo.speakers} speakers <span>·</span>
					{minutes(data.demo.durationMs)} <span>·</span> Click a word to seek
				</p>
			</div>
			<Player src="{base}/demo/{data.demo.filename}" fallbackTitle={data.demo.title} compact />
			<div class="example-bottom">
				<span>Audio + transcript, from the same file</span>
				<a href="{base}/demo/{data.demo.filename}" download
					>Download <span>{mb(data.demo.bytes)}</span>
					<span aria-hidden="true">↓</span></a
				>
			</div>
			<p class="fixture-note">
				Courtesy NASA/JPL-Caltech · September 15, 2017.
				<a href="https://www.jpl.nasa.gov/videos/final-moments-in-cassini-mission-control/"
					>Original video</a
				>. Transcript reconciled from multiple models and JPL captions; uncertain speech is marked.
				<a href="{base}/demo/README.md">Sources &amp; transcription notes</a>
			</p>
		</div>

		<div class="inside">
			<figure class="schematic">
				<pre><code>{tree}</code></pre>
				<figcaption>Same extension. Same audio. More to work with.</figcaption>
			</figure>
			<p class="inside-note">
				The manifest and each transcript are UTF-8 JSON, gzipped, base64url-encoded and split across
				numbered comments. These values come from the downloadable example.
			</p>
			<TagDump
				rows={data.rows}
				count={data.demo.commentCount}
				title={data.demo.filename}
				max={8}
				note="Payload values are shortened for display."
			/>
			<div class="code manifest">
				<div class="code__bar"><span>Decoded manifest</span></div>
				{@html data.manifestHtml}
			</div>
			<a class="text-link" href="{base}/consume/">Learn how to extract and verify the payload →</a>
		</div>
	</div>

	<p class="size-note">
		In this example, the compressed manifest and transcript total <strong
			>{(data.demo.gzipBytes / 1024).toFixed(1)} KB</strong
		>
		in a <strong>{mb(data.demo.bytes)}</strong> file. These sizes exclude base64 encoding and tag overhead.
	</p>
</section>

<section class="shell section" id="spec" aria-labelledby="spec-title">
	<div class="section-heading">
		<h2 id="spec-title">Specification</h2>
	</div>

	<a class="current" href="{base}/spec/v1/">
		<p class="eyebrow eyebrow--plain">Current version · Published 2 September 2026</p>
		<h3>Cassini v1 <span aria-hidden="true">→</span></h3>
		<p class="current-what">
			The file structure, metadata, producer requirements and reader behavior.
		</p>
	</a>

	<div class="cards">
		<a href="{base}/spec/words-v1/">
			<h3>Transcript body</h3>
			<p>A word, its speaker, and start and end times in milliseconds.</p>
			<code>cassini.words.v1</code>
		</a>
		<a href="{base}/spec/audio-integrity/">
			<h3>Audio digest</h3>
			<p>The exact bytes used to match a transcript to a recording, independent of its tags.</p>
			<code>exact-opus-audio-v1</code>
		</a>
		<a href="{base}/schema/">
			<h3>JSON Schemas</h3>
			<p>Validate the manifest and transcript body. Served at stable URLs, CC0.</p>
			<code>/schema/</code>
		</a>
		<a href="{base}/changelog/">
			<h3>Latest change</h3>
			<p>{data.change.date} — {data.change.title}</p>
			<code>changelog</code>
		</a>
	</div>
</section>

<section class="shell section" id="tools" aria-labelledby="tools-title">
	<div class="section-heading">
		<h2 id="tools-title">Tools</h2>
	</div>
	<ul class="tools">
		{#each tools as tool (tool.name)}
			<li>
				<a href={tool.href}
					><strong>{tool.name}</strong><span class="tool-what">{tool.what}</span><span
						class="tool-meta">{tool.meta}</span
					></a
				>
			</li>
		{/each}
	</ul>
	<p class="tools-more"><a href="{base}/build/">All the tools, with language and licence →</a></p>
</section>

<section class="shell section" id="implementations" aria-labelledby="implementations-title">
	<div class="section-heading">
		<h2 id="implementations-title">Implementations</h2>
	</div>

	<div class="impl">
		<article>
			<p>
				gocassini is the reference implementation. It records Nextcloud Talk calls, transcribes them
				and saves each meeting as a Cassini file. Open source, installed as a Nextcloud app.
			</p>
			<div class="impl-links">
				<a href={site.appUrl} rel="noreferrer">gocassini.com ↗</a>
				<a href={site.implRepo} rel="noreferrer">Source on GitHub ↗</a>
				<a href="https://apps.nextcloud.com/apps/gocassini" rel="noreferrer">Nextcloud app ↗</a>
			</div>
		</article>
	</div>
</section>

<style>
	.hero {
		padding-block: clamp(3rem, 6vw, 5.5rem) 1rem;
		max-width: 1000px;
		margin-inline: auto;
	}
	.release {
		display: inline-flex;
		margin-top: 1.6rem;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.5rem;
		font: 11px var(--mono);
		color: var(--fg-3);
	}
	.release code {
		font-size: 11px;
		padding: 0.06em 0.36em;
	}
	.release-dot {
		width: 6px;
		height: 6px;
		background: var(--green);
		border-radius: 50%;
		flex: none;
	}
	.release-divider {
		color: var(--fg-5);
	}
	h1 {
		font-size: clamp(3rem, 5.3vw, 4.8rem);
		line-height: 1.04;
		letter-spacing: -0.06em;
		margin: 0 0 1.6rem;
	}
	h1 > span {
		color: var(--blue);
	}
	.hero-lede {
		color: var(--fg);
		font-size: clamp(1.1rem, 1.35vw, 1.3rem);
		line-height: 1.45;
		max-width: 52ch;
		margin-bottom: 0.85rem;
	}
	.hero-description {
		max-width: 62ch;
		font-size: 16px;
	}
	.hero .actions {
		margin-top: 1.1rem;
	}

	.section {
		padding-top: clamp(3.5rem, 7vw, 6rem);
	}
	.section-heading {
		max-width: 760px;
		margin-bottom: 2.25rem;
	}
	.section-heading h2 {
		margin-bottom: 0;
	}

	/* ---- the example, in one block ---- */
	.proof {
		display: grid;
		grid-template-columns: 1.05fr 0.95fr;
		gap: 2.5rem;
		align-items: start;
	}
	.example {
		min-width: 0;
		border: 1px solid var(--rule-hi);
		border-radius: 9px;
		background: var(--bg-raise);
		box-shadow: 0 18px 60px #00000012;
	}
	.example-top {
		display: flex;
		align-items: center;
		justify-content: space-between;
		border-bottom: 1px solid var(--rule);
		padding: 1rem 1.3rem;
	}
	.example-top .eyebrow {
		color: var(--blue);
	}
	.file-type {
		font: 11px var(--mono);
		color: var(--fg-4);
	}
	.example-heading {
		padding: 1.3rem 1.3rem 1rem;
	}
	.example-heading h3 {
		font-size: 19px;
		line-height: 1.4;
		letter-spacing: -0.02em;
	}
	.example-heading p {
		font-size: 12px;
		margin: 0.45rem 0 0;
		color: var(--fg-4);
	}
	.example-heading p span {
		margin-inline: 0.25rem;
	}
	.example-bottom {
		display: flex;
		flex-wrap: wrap;
		justify-content: space-between;
		gap: 0.5rem;
		padding: 0.9rem 1.3rem;
		font-size: 11px;
		border-top: 1px solid var(--rule);
		color: var(--fg-4);
	}
	.example-bottom a {
		font-weight: 600;
	}
	.example-bottom a span {
		margin-left: 0.2rem;
	}
	.fixture-note {
		padding: 0 1.3rem 1rem;
		margin: 0;
		font-size: 11px;
		color: var(--fg-4);
		max-width: none;
	}
	.fixture-note a {
		color: inherit;
		text-decoration: underline;
	}
	.inside {
		min-width: 0;
		display: grid;
		gap: 1rem;
	}
	.schematic {
		margin: 0;
		border: 1px solid var(--rule);
		background: var(--bg-raise);
	}
	.schematic pre {
		margin: 0;
		padding: 0.9rem 1rem 0.5rem;
		font-size: 12.5px;
		line-height: 1.6;
		color: var(--fg-2);
		overflow-x: auto;
	}
	.schematic code {
		background: none;
		border: 0;
		padding: 0;
	}
	.schematic figcaption {
		padding: 0 1rem 0.8rem;
		font-size: 11px;
		color: var(--fg-4);
	}
	.inside-note {
		font-size: 14px;
		margin: 0;
	}
	.manifest {
		max-height: 420px;
		overflow: auto;
	}
	.size-note {
		font-size: 12px;
		color: var(--fg-4);
		margin-top: 1.5rem;
		max-width: 100ch;
	}
	.size-note strong {
		color: var(--fg-2);
	}

	/* ---- spec ---- */
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
	.current h3 {
		grid-area: title;
		margin: 0;
		font-size: 25px;
		white-space: nowrap;
	}
	.current h3 span {
		color: var(--blue);
		margin-left: 0.5rem;
	}
	.current-what {
		grid-area: what;
		margin: 0;
		font-size: 15px;
	}
	.cards {
		display: grid;
		grid-template-columns: repeat(4, minmax(0, 1fr));
		gap: 1rem;
		margin-top: 1rem;
	}
	.cards a {
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
		padding: 1.25rem;
		border: 1px solid var(--rule);
		border-radius: 6px;
		color: inherit;
	}
	.cards a:hover {
		background: var(--bg-raise);
		text-decoration: none;
		border-color: var(--rule-hi);
	}
	.cards h3 {
		margin: 0;
		font-size: 17px;
	}
	.cards p {
		margin: 0;
		font-size: 14px;
	}
	.cards code {
		margin-top: auto;
		font-size: 11px;
		align-self: flex-start;
	}

	/* ---- tools ---- */
	.tools {
		list-style: none;
		margin: 0;
		padding: 0;
		border-top: 1px solid var(--rule);
	}
	.tools a {
		display: grid;
		grid-template-columns: 13rem minmax(0, 1fr) 11rem;
		gap: 1rem;
		align-items: baseline;
		padding: 1rem 0;
		border-bottom: 1px solid var(--rule);
		color: inherit;
	}
	.tools a:hover {
		text-decoration: none;
		background: var(--bg-raise);
	}
	.tools strong {
		color: var(--blue);
		font-size: 15px;
		font-weight: 600;
	}
	.tool-what {
		font-size: 14px;
		color: var(--fg-2);
	}
	.tool-meta {
		font: 11px var(--mono);
		color: var(--fg-4);
		text-align: right;
	}
	.tools-more {
		margin-top: 1.25rem;
		font-size: 14px;
	}

	/* ---- implementations ---- */
	.impl {
		max-width: 760px;
	}
	.impl article {
		border-top: 1px solid var(--rule-hi);
		padding-top: 1.4rem;
		min-width: 0;
	}
	.impl p {
		font-size: 15px;
	}
	.impl-links {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem 1.5rem;
		font-size: 14px;
	}

	@media (max-width: 1050px) {
		h1 {
			font-size: 3.7rem;
		}
		.proof {
			gap: 2rem;
		}
		.cards {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}
	}
	@media (max-width: 900px) {
		.proof {
			grid-template-columns: minmax(0, 1fr);
		}
		.tools a {
			grid-template-columns: minmax(0, 1fr);
			gap: 0.3rem;
		}
		.tool-meta {
			text-align: left;
		}
	}
	@media (max-width: 820px) {
		h1 {
			font-size: clamp(3.4rem, 9vw, 5rem);
		}
	}
	@media (max-width: 560px) {
		.cards {
			grid-template-columns: minmax(0, 1fr);
		}
		.example-bottom {
			font-size: 12px;
		}
		.current {
			padding: 1.25rem;
			grid-template-columns: minmax(0, 1fr);
			grid-template-areas: 'meta' 'title' 'what';
		}
	}
</style>
