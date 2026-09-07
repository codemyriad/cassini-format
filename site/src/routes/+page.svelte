<script lang="ts">
	import { base } from '$app/paths';
	import { site } from '$lib/site';
	import TagDump from '$lib/components/TagDump.svelte';
	import Player from '$lib/components/Player.svelte';

	let { data } = $props();

	const kb = (n: number) => `${Math.round(n / 1024).toLocaleString()} KB`;
	const mb = (n: number) => `${(n / 1024 / 1024).toFixed(2)} MB`;
	const mins = (ms: number) => {
		const total = Math.round(ms / 1000);
		return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, '0')}`;
	};
	const pct = $derived(((data.demo.gzipBytes / data.demo.bytes) * 100).toFixed(1));
</script>

<svelte:head>
	<title>Cassini — an audio file format with the transcript embedded</title>
	<meta name="description" content={site.description} />
</svelte:head>

<section class="hero shell">
	<p class="kicker">
		<span class="tick">{site.formatId}</span>
		<span class="sep">·</span>
		<span>audio/ogg</span>
		<span class="sep">·</span>
		<span>no new extension</span>
	</p>

	<h1>An ordinary audio file that carries its own transcript.</h1>

	<p class="lede">
		A Cassini file is a normal <code>.opus</code> recording: Ogg Opus at 48&nbsp;kHz, and any player
		plays it. It also carries who spoke, what they said with word-level timestamps, and what
		produced that text, embedded in the same place <code>TITLE</code> and <code>ARTIST</code> live.
		One file format for audio and text, with no sidecar to lose.
	</p>

	<div class="hero__dump">
		<TagDump
			rows={data.rows}
			count={data.demo.commentCount}
			title="lantern-festival.opus"
			command="ffprobe -v error -show_entries stream_tags -of default=nw=1 meeting.opus"
			max={14}
			note="Real output, with the payload chunks hidden. Tags sort ASCII: that is the order the producer writes them."
		/>
	</div>

	<div class="cta">
		<a class="btn btn--go" href="{base}/spec/v1/">Read the spec</a>
		<a class="btn" href="{base}/consume/">Read a file</a>
		<a class="btn" href="{base}/produce/">Write a file</a>
		<a class="btn btn--dl" href="{base}/demo/lantern-festival.opus" download>
			Download that file <span>{mb(data.demo.bytes)}</span>
		</a>
	</div>
</section>

<section class="shell band">
	<p class="eyebrow">Three commitments</p>
	<div class="grid grid--3">
		<div class="cell">
			<p class="n">01</p>
			<h3>It degrades to audio</h3>
			<p>
				Understand nothing and you still play the recording. Understand the tags and you get
				everything.
			</p>
		</div>
		<div class="cell">
			<p class="n">02</p>
			<h3>Keep what a better model could use</h3>
			<p>
				The original words and their timings stay available beside display text, with provenance
				naming the engine, model and device. Another model's transcript can live in the same file
				for comparison.
			</p>
		</div>
		<div class="cell">
			<p class="n">03</p>
			<h3>The digest binds transcript to recording</h3>
			<p>
				A SHA-256 over the Opus packets, answering one question: is this transcript describing this
				recording? It catches accidents, not adversaries.
			</p>
		</div>
	</div>
</section>

<section class="shell band">
	<p class="eyebrow">See for yourself</p>
	<div class="two">
		<div>
			<p>
				Two layers. The first is plain tags any tool shows: title, date, speaker count,
				the digests, and a decode hint explaining the second layer in one sentence. Someone with
				<code>ffprobe</code> and no documentation should be able to work this out alone.
			</p>
			<p>
				The second is the payload: compact UTF-8 JSON, gzipped, base64url-encoded, split across
				numbered tags small enough to keep the comment header readable. It decodes in one pipeline,
				using nothing you don't already have.
			</p>
			<p class="muted">
				The <code>awk</code> line re-pads: the producer writes unpadded base64url and GNU
				<code>basenc</code> demands padding.
			</p>
		</div>
		<div class="code">
			<div class="code__bar">
				<span>bash</span><button class="copy" type="button" data-copy>copy</button>
			</div>
			{@html data.decodeHtml}
		</div>
	</div>

	<div class="two two--tight">
		<div class="code">
			<div class="code__bar"><span>the manifest that comes out</span></div>
			{@html data.manifestHtml}
		</div>
		<div class="code">
			<div class="code__bar"><span>and a transcript body, one item per word</span></div>
			{@html data.wordsHtml}
		</div>
	</div>
</section>

<section class="shell band">
	<p class="eyebrow">Try it on the actual file</p>
	<p class="lede">
		Nothing is loaded from anywhere else. The player fetches the same <code>.opus</code> you can
		download, walks its Ogg pages in JavaScript, reassembles the chunks, inflates them with
		<code>DecompressionStream</code>, checks the manifest and transcript digests, and plays. The audio
		digest is not checked in the browser, so the reader says <code>unverified</code>, as the spec
		requires.
	</p>
	<p class="muted">
		The words are the script the voices read, with timings derived from the speech renderer.
		Segment timings are measured from the render; word timings inside a segment are interpolated,
		and the file says so.
	</p>
	<Player
		src="{base}/demo/lantern-festival.opus"
		fallbackTitle={data.demo.title}
	/>
</section>

<section class="shell band">
	<p class="eyebrow">Where it comes from</p>
	<div class="grid grid--2">
		<div class="cell">
			<h3>gocassini</h3>
			<p>
				We built gocassini to record and transcribe Nextcloud Talk calls, and it writes every meeting
				this way. It is the reference producer and reader, AGPL-3.0, and so far the only one in use.
			</p>
			<p><a href={site.implRepo} rel="noreferrer">github.com/codemyriad/gocassini ↗</a></p>
		</div>
		<div class="cell">
			<h3>Published so you can use it too</h3>
			<p>
				This repository has three readers and a complete producer, all CC0: a Python extractor over
				<code>ffprobe</code>, one with no external tools, a browser reader with no dependencies, and a
				producer in stdlib Python. The same format carries
				<a href="{base}/demo/">a song with synchronized lyrics in one audio file</a> as easily as
				a meeting.
			</p>
			<p>
				<a href="{base}/consume/">Read one</a> · <a href="{base}/produce/">Write one</a> ·
				<a href="{base}/llms-full.txt">the whole spec in one file</a> ·
				<a href="{base}/status/">status</a>
			</p>
		</div>
	</div>
</section>

<section class="shell band">
	<p class="eyebrow">What it costs</p>
	<div class="grid grid--2 stats">
		<div>
			<p class="stat">{pct}%</p>
			<p class="statlab">
				of the demo file is transcript: {kb(data.demo.gzipBytes)} on {mb(data.demo.bytes)} of audio.
			</p>
		</div>
		<div>
			<p class="stat">{data.demo.words.toLocaleString()}</p>
			<p class="statlab">
				word-timed items, {data.demo.speakers} speakers, {mins(data.demo.durationMs)} of speech, in
				{data.demo.commentCount} Vorbis comments.
			</p>
		</div>
	</div>
</section>

<section class="shell band">
	<p class="eyebrow">What it doesn't do</p>
	<div class="grid grid--2">
		<div class="cell">
			<h3>It doesn't model transcript history</h3>
			<p>
				A reprocessed file replaces its predecessor. Provenance records what made the current
				transcript, not what came before.
			</p>
		</div>
		<div class="cell">
			<h3>It doesn't survive audio edits</h3>
			<p>
				Cut the audio in an editor that has never heard of Cassini and the digest stops matching.
				What is left is a plain recording with stale metadata.
			</p>
		</div>
		<div class="cell">
			<h3>It doesn't prove authenticity</h3>
			<p>
				Anyone who rewrites the transcript can recompute every hash and the file still verifies.
			</p>
		</div>
		<div class="cell">
			<h3>It doesn't claim a name of its own</h3>
			<p>
				No new extension, media type or magic bytes: the file is <code>audio/ogg</code>. It has to
				keep working in software that will never be updated for it.
			</p>
		</div>
	</div>
</section>

<style>
	.hero {
		/* Block only: .shell owns the inline gutter, and the `padding`
		   shorthand would reset it to zero. */
		padding-block: clamp(3rem, 8vh, 6rem) 1rem;
	}
	.kicker {
		display: flex;
		flex-wrap: wrap;
		align-items: baseline;
		gap: 0 0.5rem;
		margin: 0;
		font-size: 11px;
		line-height: 1.7;
		letter-spacing: 0.14em;
		text-transform: uppercase;
		color: var(--fg-4);
		max-width: none;
	}
	.tick {
		color: var(--blue);
	}
	.sep {
		color: var(--fg-5);
		margin: 0 0.15rem;
	}
	.hero h1 {
		margin: 1.4rem 0 1.6rem;
		max-width: 22ch;
	}
	.hero .lede + .lede {
		color: var(--fg-3);
	}
	.hero__dump {
		margin: 2.2rem 0 1.6rem;
	}
	.cta {
		display: flex;
		flex-wrap: wrap;
		gap: 0.6rem;
	}
	.btn {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		border: 1px solid var(--rule);
		background: var(--bg-raise);
		color: var(--fg-2);
		padding: 0.5rem 0.9rem;
		font-size: 13px;
	}
	.btn:hover {
		color: var(--fg);
		border-color: var(--rule-hi);
		background: var(--bg-raise-hi);
		text-decoration: none;
	}
	.btn--go {
		border-color: var(--blue-rule);
		background: var(--blue-wash);
		color: var(--blue);
	}
	.btn--go:hover {
		color: var(--blue);
		border-color: var(--blue);
	}
	.btn--dl span {
		color: var(--fg-5);
		font-size: 11px;
	}

	.band {
		padding-top: 4.5rem;
	}
	.band > .eyebrow {
		margin-bottom: 1.6rem;
	}
	.band > .lede {
		margin-bottom: 1.8rem;
	}

	.two {
		display: grid;
		grid-template-columns: minmax(0, 0.95fr) minmax(0, 1.05fr);
		gap: 2rem;
		align-items: start;
	}
	.two--tight {
		margin-top: 1.5rem;
		gap: 1rem;
	}
	@media (max-width: 950px) {
		.two {
			grid-template-columns: minmax(0, 1fr);
		}
	}

	.muted {
		color: var(--fg-4);
		font-size: 13px;
	}

	.cell .n {
		color: var(--fg-5);
		font-size: 11px;
		letter-spacing: 0.14em;
		margin: 0 0 0.6rem;
	}
	.cell h3 {
		margin-bottom: 0.55rem;
	}
	.cell p:last-child {
		margin-bottom: 0;
	}
	.cell p {
		font-size: 13.5px;
		color: var(--fg-3);
	}

	.stats .stat {
		font-size: clamp(1.8rem, 1.4rem + 1.6vw, 2.4rem);
		color: var(--blue);
		font-weight: 700;
		letter-spacing: -0.02em;
		margin: 0 0 0.5rem;
		line-height: 1;
	}
	.statlab {
		font-size: 13px;
		color: var(--fg-3);
		margin: 0;
	}
</style>
