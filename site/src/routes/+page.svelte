<script lang="ts">
	import { base } from '$app/paths';
	import { site } from '$lib/site';
	import TagDump from '$lib/components/TagDump.svelte';
	import Player from '$lib/components/Player.svelte';

	let { data } = $props();
	let layer = $state(1);
	const mb = (n: number) => `${(n / 1024 / 1024).toFixed(2)} MB`;
	const minutes = (ms: number) =>
		`${Math.floor(ms / 60000)}:${String(Math.floor((ms % 60000) / 1000)).padStart(2, '0')}`;
	const layers = [
		{
			name: 'Audio',
			detail: 'The original recording',
			label: 'Plays in an ordinary Opus player',
			description:
				'The recording is standard Ogg Opus audio. Players that do not understand Cassini can still play it. Adding a transcript leaves the compressed audio packets intact.',
			code: 'meeting.opus\n├── OpusHead   codec information\n├── OpusTags   embedded metadata\n└── Opus audio recording'
		},
		{
			name: 'Transcript',
			detail: 'Every word, with its time',
			label: 'Words you can read, search and seek',
			description:
				'Word timestamps and speaker labels live in the audio file’s comment header. A Cassini reader lets you find a passage and listen to check the words. Multiple transcripts can share the same recording.',
			code: ''
		},
		{
			name: 'Context',
			detail: 'Speakers, source and integrity',
			label: 'Enough context to use it again',
			description:
				'A manifest connects the speakers and transcripts, with optional processing provenance. An audio digest lets a reader check whether the transcript still belongs to this recording.',
			code: 'OpusTags\n├── Title and readable summary tags\n├── Manifest → speakers, transcripts\n├── Transcript bodies → timed words\n└── Audio digest → recording match'
		}
	];
</script>

<svelte:head>
	<title>Cassini — the recording, the words, one file</title>
	<meta name="description" content={site.description} />
</svelte:head>

<section class="hero shell" aria-labelledby="hero-title">
	<div class="hero-copy">
		<a class="release" href="{base}/status/"
			><span class="release-dot"></span> Open format
			<span class="release-divider">/</span>
			Version 1 <span aria-hidden="true">↗</span></a
		>
		<h1 id="hero-title">
			The recording.<br />The words.<br /><span>One file.</span>
		</h1>
		<p class="hero-lede">Find a passage in the transcript. Hear what was actually said.</p>
		<p class="hero-description">
			Transcriptions can get words wrong. Cassini keeps the audio and timed transcript in one
			<code>.opus</code> file so you can listen and check. We (<a href={site.companyUrl}>codemyriad</a>) made it for
			<a href={site.implRepo}>our Nextcloud Talk app</a> and use it for our own meetings.
		</p>
		<div class="actions">
			<a class="button button--primary" href="{base}/try/"
				>Try a file <span aria-hidden="true">→</span></a
			>
			<a class="button" href="{base}/using/">How it fits your workflow</a>
		</div>
		<p class="hero-note">Standard Ogg Opus. Open specification. No sidecar to lose.</p>
	</div>

	<div class="example" id="example">
		<div class="example-top">
			<span class="eyebrow eyebrow--plain">Listen & follow along</span><span class="file-type"
				>.opus</span
			>
		</div>
		<div class="example-heading">
			<h2>{data.demo.title}</h2>
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
			<a href="https://www.jpl.nasa.gov/videos/final-moments-in-cassini-mission-control/">Original video</a>.
			Transcript reconciled from multiple models and JPL captions; uncertain speech is marked.
			<a href="{base}/demo/README.md">Sources & transcription notes</a>
		</p>
	</div>
</section>

<div class="shell">
	<div class="facts" aria-label="Format at a glance">
		<div>
			<strong>One .opus file</strong><span>Audio and text together</span>
		</div>
		<div>
			<strong>Word-level timing</strong><span>Find a passage and listen back</span>
		</div>
		<div>
			<strong>Ordinary playback</strong><span>Works in players that support Opus</span>
		</div>
		<div>
			<strong>Open to implement</strong><span>CC0 schemas and reader code</span>
		</div>
	</div>
</div>

<section class="shell section" id="build" aria-labelledby="build-title">
	<div class="section-heading">
		<p class="eyebrow eyebrow--plain">01 / Your next step</p>
		<h2 id="build-title">What brings you here?</h2>
		<p>Explore where the format fits, use a recording, or bring Cassini into your own software.</p>
	</div>
	<div class="paths">
		<a class="path" href="{base}/using/"
			><span class="path-label">Understand & decide</span>
			<h3>See how it fits <span aria-hidden="true">→</span></h3>
			<p>
				What you start with, what travels with the file, and what someone else needs to use it.
			</p>
			<span class="path-meta">Workflows, compatibility & limits</span></a
		>
		<a class="path" href="{base}/try/"
			><span class="path-label">Listen & read</span>
			<h3>Open a recording <span aria-hidden="true">→</span></h3>
			<p>
				Follow the sample or open a file someone sent you. Find a passage and listen to check the words.
			</p>
			<span class="path-meta">In your browser · local files stay local</span></a
		>
		<a class="path" href="{base}/build/"
			><span class="path-label">Integrate & create</span>
			<h3>Build with Cassini <span aria-hidden="true">→</span></h3>
			<p>
				Extract transcript data, create portable recordings, or implement the format in your own stack.
			</p>
			<span class="path-meta">Working guides, reference & checks</span></a
		>
	</div>
	<div class="build-note">
		<p>Already implementing?</p>
		<a href="{base}/spec/"
			>Go straight to the specification & schemas <span aria-hidden="true">→</span></a
		>
	</div>
</section>

<section class="shell section" aria-labelledby="why-title">
	<div class="section-heading">
		<p class="eyebrow eyebrow--plain">02 / From one tool to the next</p>
		<h2 id="why-title">
			Keep a way back<br />to what was said.
		</h2>
		<p>
			A transcript makes a recording easier to navigate. Keeping the audio with it lets you listen
			for yourself, even after someone saves or shares the file.
		</p>
	</div>
	<div class="benefits">
		<article>
			<span class="benefit-mark" aria-hidden="true">01</span>
			<h3>Bring audio and words together</h3>
			<p>
				Start with a recording and a timed transcript. A <a href="{base}/produce/">producer</a>
				packages them into one file. You choose what records and transcribes the audio.
			</p>
		</article>
		<article>
			<span class="benefit-mark" aria-hidden="true">02</span>
			<h3>Send the whole conversation</h3>
			<p>
				Copy or share the <code>.opus</code> file. Its words and speaker labels travel with it,
				without another attachment or access to the service that made it.
			</p>
		</article>
		<article>
			<span class="benefit-mark" aria-hidden="true">03</span>
			<h3>Listen and check the words</h3>
			<p>
				Find a passage in a <a href="{base}/try/">Cassini reader</a> and listen back. The recording
				stays available when you need to check a name, a number or the meaning of a reply.
			</p>
		</article>
	</div>
</section>

<section class="shell section" aria-labelledby="inside-title">
	<div class="section-heading">
		<p class="eyebrow eyebrow--plain">03 / How it stays portable</p>
		<h2 id="inside-title">Audio underneath. Context built in.</h2>
		<p>
			Cassini adds metadata where an audio file already keeps its title and artist: the OpusTags
			header.
		</p>
	</div>
	<div class="anatomy">
		<div class="file-stack" aria-label="Explore the file layers">
			<div class="file-stack-title">
				<svg
					width="20"
					height="24"
					viewBox="0 0 20 24"
					fill="none"
					stroke="currentColor"
					aria-hidden="true"><path d="M2 1h10l6 6v16H2zM12 1v6h6" /></svg
				><span>meeting.opus</span><span class="stack-note">one file</span>
			</div>
			{#each layers as item, i (item.name)}
				<button
					class="layer"
					class:selected={layer === i}
					aria-pressed={layer === i}
					aria-controls="layer-detail"
					onclick={() => (layer = i)}
					><span class="layer-number">0{i + 1}</span><span
						><strong>{item.name}</strong><small>{item.detail}</small></span
					><span class="layer-arrow" aria-hidden="true">↗</span></button
				>
			{/each}
			<p class="stack-caption">Same extension. Same audio. More to work with.</p>
		</div>
		<div class="layer-detail" id="layer-detail" aria-live="polite" aria-atomic="true">
			<p class="eyebrow eyebrow--plain">{layers[layer].name}</p>
			<h3>{layers[layer].label}</h3>
			<p>{layers[layer].description}</p>
			<div class="code">
				<div class="code__bar">
					<span>{layer === 1 ? 'A word from the example file' : 'File structure · schematic'}</span>
				</div>
				{#if layer === 1}{@html data.wordHtml}{:else}<pre><code>{layers[layer].code}</code
						></pre>{/if}
			</div>
		</div>
	</div>
	<details class="inspect">
		<summary
			><span>Look at the actual tags and decoded manifest</span><span class="inspect-hint"
				>For a closer look</span
			></summary
		>
		<div class="inspect-body">
			<p>
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
			<div class="code">
				<div class="code__bar"><span>Decoded manifest</span></div>
				{@html data.manifestHtml}
			</div>
			<a class="text-link" href="{base}/consume/">Learn how to extract and verify the payload →</a>
		</div>
	</details>
	<p class="size-note">
		In this example, the compressed manifest and transcript total <strong
			>{(data.demo.gzipBytes / 1024).toFixed(1)} KB</strong
		>
		in a <strong>{mb(data.demo.bytes)}</strong> file. These sizes exclude base64 encoding and tag overhead.
	</p>
</section>

<section class="shell section questions" aria-labelledby="questions-title">
	<div class="section-heading">
		<p class="eyebrow eyebrow--plain">Before you choose</p>
		<h2 id="questions-title">A small format, with some limits.</h2>
		<p>
			We vibe coded this and use it in <a href={site.implRepo}>gocassini</a> for our own meetings.
			Version 1 is published, but independent adoption is still something we hope to see.
			<a href="{base}/status/">Read the project status →</a>
		</p>
	</div>
	<div class="faq">
		<details>
			<summary>Does Cassini create the transcript?</summary>
			<p>
				The format stores a transcript you already have. Recording and speech recognition happen in
				a producer such as <a href={site.implRepo}>gocassini</a>. The standalone Python producer
				takes audio and timed words as input.
			</p>
		</details>
		<details>
			<summary>Do listeners need a Cassini app?</summary>
			<p>
				They need a player that supports Ogg Opus to hear the audio. A Cassini reader is needed to
				display the embedded words and speaker labels. <a href="{base}/try/">The browser reader</a> is
				one example.
			</p>
		</details>
		<details>
			<summary>What happens if the audio is edited?</summary>
			<p>
				Audio edits can leave the embedded transcript out of date. A reader that checks the audio
				digest can detect a mismatch and label the transcript as stale. Software may also strip
				metadata, so check files after editing or converting them.
			</p>
		</details>
		<details>
			<summary>Do the digests prove authenticity?</summary>
			<p>
				No. They check that data matches, including whether a transcript refers to the same audio.
				Anyone rewriting a file can recompute its hashes. Cassini does not provide signatures or
				proof of who said something.
			</p>
		</details>
		<details>
			<summary>Can I implement it in my own software?</summary>
			<p>
				Yes. The schemas, test vectors and standalone readers and producer are CC0. The
				specification text is CC BY 4.0. The transcript interface shown here comes from Cassini and
				is AGPL-3.0, as is the gocassini application. <a href="{base}/spec/"
					>Start with the reference →</a
				>
			</p>
		</details>
	</div>
</section>

<style>
	.hero {
		display: grid;
		grid-template-columns: 0.95fr 1.05fr;
		gap: clamp(2rem, 5vw, 4.5rem);
		align-items: center;
		padding-block: clamp(3rem, 6vw, 5.5rem) 4rem;
	}
	.hero-copy {
		min-width: 0;
	}
	.release {
		display: inline-flex;
		align-items: center;
		gap: 0.65rem;
		font: 11px var(--mono);
		color: var(--fg-3);
	}
	.release-dot {
		width: 6px;
		height: 6px;
		background: var(--green);
		border-radius: 50%;
	}
	.release-divider {
		color: var(--fg-5);
	}
	h1 {
		font-size: clamp(3rem, 5.3vw, 4.8rem);
		line-height: 1.04;
		letter-spacing: -0.06em;
		margin: 1.6rem 0;
	}
	h1 > span {
		color: var(--blue);
	}
	.hero-lede {
		color: var(--fg);
		font-size: clamp(1.15rem, 1.5vw, 1.4rem);
		line-height: 1.4;
		max-width: 30ch;
		margin-bottom: 0.85rem;
	}
	.hero-description {
		max-width: 46ch;
		font-size: 16px;
	}
	.hero .actions {
		margin-top: 1.8rem;
	}
	.hero-note {
		margin: 1.1rem 0 0;
		color: var(--fg-4);
		font-size: 12px;
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
	.example-heading h2 {
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
	}
	.fixture-note a {
		color: inherit;
		text-decoration: underline;
	}
	.facts {
		display: grid;
		grid-template-columns: repeat(4, minmax(0, 1fr));
		gap: 1.5rem;
		border-block: 1px solid var(--rule);
		padding-block: 1.75rem;
	}
	.facts div {
		display: grid;
		gap: 0.3rem;
	}
	.facts strong {
		color: var(--fg);
		font-size: 14px;
		font-weight: 600;
	}
	.facts span {
		font-size: 12px;
		color: var(--fg-4);
	}
	.section {
		padding-top: clamp(4rem, 8vw, 6.5rem);
	}
	.section-heading {
		max-width: 700px;
		margin-bottom: 2.5rem;
	}
	.section-heading .eyebrow {
		color: var(--blue);
		margin-bottom: 1rem;
	}
	.section-heading h2 {
		margin-bottom: 1rem;
	}
	.section-heading > p:last-child {
		max-width: 59ch;
		margin-bottom: 0;
		font-size: 16px;
	}
	.benefits {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		gap: 2.5rem;
	}
	.benefits article {
		border-top: 1px solid var(--rule-hi);
		padding-top: 1.4rem;
	}
	.benefit-mark {
		color: var(--blue);
		font: 26px var(--mono);
	}
	.benefits h3 {
		margin: 1rem 0 0.7rem;
	}
	.benefits p {
		font-size: 15px;
		margin: 0;
	}
	.anatomy {
		display: grid;
		grid-template-columns: 0.9fr 1.1fr;
		gap: 4rem;
		align-items: start;
	}
	.file-stack {
		border: 1px solid var(--rule-hi);
		border-radius: 7px;
		overflow: hidden;
	}
	.file-stack-title {
		display: flex;
		gap: 0.75rem;
		align-items: center;
		padding: 1.25rem;
		font: 14px var(--mono);
		color: var(--fg);
		border-bottom: 1px solid var(--rule);
	}
	.file-stack-title svg {
		color: var(--blue);
	}
	.stack-note {
		margin-left: auto;
		color: var(--fg-4);
		font-size: 11px;
	}
	.layer {
		display: flex;
		align-items: center;
		gap: 1rem;
		width: 100%;
		padding: 1.15rem 1.25rem;
		text-align: left;
		border: 0;
		border-bottom: 1px solid var(--rule);
		background: transparent;
		color: var(--fg-2);
		cursor: pointer;
	}
	.layer:hover {
		background: var(--bg-raise);
	}
	.layer.selected {
		background: var(--blue-wash);
		box-shadow: inset 3px 0 var(--blue);
	}
	.layer:focus-visible {
		outline-offset: -3px;
	}
	.layer-number {
		font: 11px var(--mono);
		color: var(--fg-4);
	}
	.layer strong {
		display: block;
		font-size: 17px;
		font-weight: 600;
		color: var(--fg);
	}
	.layer small {
		font-size: 13px;
		color: var(--fg-4);
	}
	.layer-arrow {
		margin-left: auto;
		color: var(--fg-4);
	}
	.layer.selected .layer-arrow,
	.layer.selected strong {
		color: var(--blue);
	}
	.stack-caption {
		margin: 0;
		padding: 0.9rem 1.25rem;
		font-size: 12px;
		color: var(--fg-4);
	}
	.layer-detail {
		min-width: 0;
	}
	.layer-detail .eyebrow {
		margin: 0.3rem 0 1rem;
	}
	.layer-detail h3 {
		margin-bottom: 0.8rem;
	}
	.layer-detail > p {
		font-size: 15px;
	}
	.layer-detail .code {
		border-radius: 5px;
	}
	.layer-detail .code pre {
		min-height: 165px;
	}
	.inspect {
		border-block: 1px solid var(--rule);
		margin-top: 2.5rem;
	}
	.inspect summary {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		cursor: pointer;
		padding-block: 1.1rem;
		font-size: 14px;
		color: var(--fg);
		list-style: none;
	}
	.inspect summary::before {
		content: '+';
		color: var(--blue);
		font: 18px var(--mono);
	}
	.inspect[open] summary::before {
		content: '−';
	}
	.inspect summary::-webkit-details-marker {
		display: none;
	}
	.inspect-hint {
		margin-left: auto;
		color: var(--fg-4);
		font-size: 12px;
	}
	.inspect-body {
		padding-bottom: 1.5rem;
		display: grid;
		gap: 1rem;
		min-width: 0;
	}
	.inspect-body > p {
		font-size: 14px;
		margin: 0;
	}
	.inspect-body .code {
		max-height: 420px;
		overflow: auto;
	}
	.size-note {
		font-size: 12px;
		color: var(--fg-4);
		margin-top: 1rem;
		max-width: 100ch;
	}
	.size-note strong {
		color: var(--fg-2);
	}
	.paths {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		border: 1px solid var(--rule-hi);
		border-radius: 7px;
		overflow: hidden;
	}
	.path {
		padding: 1.6rem;
		color: inherit;
		display: flex;
		flex-direction: column;
		border-right: 1px solid var(--rule);
	}
	.path:last-child {
		border: 0;
	}
	.path:hover {
		text-decoration: none;
		background: var(--blue-wash);
	}
	.path-label {
		font: 10px var(--mono);
		text-transform: uppercase;
		letter-spacing: 0.09em;
		color: var(--fg-4);
	}
	.path h3 {
		margin: 1.2rem 0 0.75rem;
		font-size: 21px;
		display: flex;
		justify-content: space-between;
		gap: 1rem;
	}
	.path h3 span {
		color: var(--blue);
	}
	.path p {
		font-size: 14px;
		margin: 0 0 1.5rem;
	}
	.path-meta {
		font-size: 12px;
		color: var(--blue);
		margin-top: auto;
	}
	.build-note {
		display: flex;
		flex-wrap: wrap;
		gap: 0.25rem 1rem;
		margin-top: 1.1rem;
		font-size: 13px;
	}
	.build-note p {
		margin: 0;
		color: var(--fg-4);
	}
	.questions {
		display: grid;
		grid-template-columns: 0.85fr 1.15fr;
		gap: 4rem;
	}
	.faq {
		border-top: 1px solid var(--rule);
	}
	.faq details {
		border-bottom: 1px solid var(--rule);
	}
	.faq summary {
		cursor: pointer;
		color: var(--fg);
		padding: 1.05rem 1.8rem 1.05rem 0;
		font-size: 16px;
		font-weight: 500;
		position: relative;
		list-style: none;
	}
	.faq summary::-webkit-details-marker {
		display: none;
	}
	.faq summary::after {
		content: '+';
		position: absolute;
		right: 0;
		color: var(--blue);
	}
	.faq details[open] summary::after {
		content: '−';
	}
	.faq p {
		font-size: 14px;
		padding-right: 1rem;
	}
	@media (max-width: 1050px) {
		.hero {
			gap: 2rem;
		}
		h1 {
			font-size: 3.7rem;
		}
		.anatomy,
		.questions {
			gap: 2rem;
		}
		.path {
			padding: 1.25rem;
		}
	}
	@media (max-width: 820px) {
		.hero {
			grid-template-columns: minmax(0, 1fr);
			gap: 2.5rem;
		}
		h1 {
			font-size: clamp(3.4rem, 9vw, 5rem);
		}
		.hero-description {
			max-width: 55ch;
		}
		.facts {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}
		.benefits {
			gap: 1.25rem;
		}
		.benefits h3 {
			font-size: 17px;
		}
		.anatomy,
		.questions {
			grid-template-columns: minmax(0, 1fr);
		}
		.questions {
			gap: 0;
		}
		.paths {
			grid-template-columns: minmax(0, 1fr);
		}
		.path {
			border-right: 0;
			border-bottom: 1px solid var(--rule);
		}
		.path h3 {
			margin-top: 0.8rem;
		}
	}
	@media (max-width: 560px) {
		.benefits {
			grid-template-columns: minmax(0, 1fr);
			gap: 2rem;
		}
		.benefits h3 {
			font-size: 20px;
			margin-top: 0.6rem;
		}
		.inspect-hint {
			display: none;
		}
		.example-bottom {
			font-size: 12px;
		}
		.facts {
			gap: 1.5rem 1rem;
		}
	}
</style>
