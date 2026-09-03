<script lang="ts">
	import { untrack } from 'svelte';
	import { base } from '$app/paths';
	import { readCassini, type ReadResult, type Word } from '$lib/reader/cassini';

	const DEMO = `${base}/demo/elements.opus`;

	let result = $state<ReadResult | null>(null);
	let error = $state('');
	let loading = $state(true);
	let sourceName = $state('elements.opus');

	let audio = $state<HTMLAudioElement | null>(null);
	let objectUrl = $state('');
	let timeMs = $state(0);
	let duration = $state(0);
	let playing = $state(false);
	let dragging = $state(false);
	let fullscreen = $state(false);
	let stageEl = $state<HTMLDivElement | null>(null);

	/**
	 * The spec is explicit that transcript items are in speaker-turn order, not
	 * time order: across a speaker change startMs goes backwards, because
	 * overlapping speech keeps each speaker's words together. A karaoke timeline
	 * is the one view that cannot live with that, so it sorts. Ties keep their
	 * original relative order, which matters when two speakers start together.
	 */
	const timeline = $derived.by<Word[]>(() => {
		const words = result?.transcript?.words;
		if (!words) return [];
		return words
			.map((w, i) => ({ w, i }))
			.sort((a, b) => a.w.startMs - b.w.startMs || a.i - b.i)
			.map(({ w }) => w);
	});

	const speakerLabel = $derived.by(() => {
		const map = new Map<string, string>();
		for (const s of result?.manifest?.speakers ?? []) map.set(s.id, s.label ?? s.id);
		return map;
	});

	/**
	 * Index of the word being sung, or the one about to be. Binary search rather
	 * than a scan: this runs every animation frame, and a long recording is
	 * thousands of words.
	 */
	const cursor = $derived.by(() => {
		const words = timeline;
		if (!words.length) return { index: -1, active: false };
		let lo = 0;
		let hi = words.length - 1;
		let candidate = -1;
		while (lo <= hi) {
			const mid = (lo + hi) >> 1;
			if (words[mid].startMs <= timeMs) {
				candidate = mid;
				lo = mid + 1;
			} else {
				hi = mid - 1;
			}
		}
		if (candidate < 0) return { index: 0, active: false };
		// Inside its own span it is being sung; past the end we are in a gap, and
		// the word stays on screen dimmed rather than the stage going blank.
		return { index: candidate, active: timeMs < words[candidate].endMs };
	});

	/**
	 * Three fixed rows: what was just sung, the word being sung, what is coming.
	 * Laying the context out as its own row rather than letting one wrapping line
	 * mix a 3rem word with 1rem ones is what keeps the stage from reflowing on
	 * every word.
	 */
	const stage = $derived.by(() => {
		const words = timeline;
		if (!words.length) return null;
		const c = cursor.index;
		return {
			before: words.slice(Math.max(0, c - 4), c),
			current: words[c],
			after: words.slice(c + 1, c + 5)
		};
	});

	const progress = $derived(duration > 0 ? Math.min(1, timeMs / duration) : 0);

	async function load(src: string | File) {
		loading = true;
		error = '';
		result = null;
		try {
			const bytes =
				src instanceof File
					? await src.arrayBuffer()
					: await (await fetch(src)).arrayBuffer();
			// Hand the same bytes to <audio>, rather than making the browser fetch
			// the file a second time.
			if (objectUrl) URL.revokeObjectURL(objectUrl);
			objectUrl = URL.createObjectURL(new Blob([bytes.slice(0)], { type: 'audio/ogg' }));
			result = await readCassini(bytes);
			sourceName = src instanceof File ? src.name : src.split('/').pop() || 'demo';
			if (!result.transcript?.words?.length) {
				error = result.cassini
					? 'That file carries no transcript this reader could load.'
					: 'That is ordinary audio with no Cassini metadata, so there are no words to show.';
			}
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			loading = false;
		}
	}

	/**
	 * ?file=/demo/something.opus makes a particular file linkable. Same-origin
	 * paths only: this fetches whatever it is handed, and a page that will fetch
	 * an arbitrary host on someone else's say-so is a page worth not writing.
	 */
	function requestedFile(): string {
		if (typeof window === 'undefined') return DEMO;
		const asked = new URLSearchParams(window.location.search).get('file');
		if (!asked) return DEMO;
		if (!asked.startsWith('/') || asked.startsWith('//')) return DEMO;
		return asked;
	}

	$effect(() => {
		untrack(() => load(requestedFile()));
	});

	/**
	 * timeupdate fires about four times a second, which reads as a stutter when a
	 * word lasts 200 ms. While playing, sample the clock every frame instead.
	 */
	$effect(() => {
		if (!playing || !audio) return;
		let raf = 0;
		const tick = () => {
			if (audio) timeMs = audio.currentTime * 1000;
			raf = requestAnimationFrame(tick);
		};
		raf = requestAnimationFrame(tick);
		return () => cancelAnimationFrame(raf);
	});

	function toggle() {
		if (!audio) return;
		if (audio.paused) audio.play();
		else audio.pause();
	}

	function seekTo(fraction: number) {
		if (!audio || !duration) return;
		audio.currentTime = (fraction * duration) / 1000;
		timeMs = fraction * duration;
	}

	function seekBy(deltaMs: number) {
		if (!audio || !duration) return;
		const next = Math.min(duration, Math.max(0, timeMs + deltaMs));
		audio.currentTime = next / 1000;
		timeMs = next;
	}

	function onScrub(event: MouseEvent) {
		const bar = event.currentTarget as HTMLElement;
		const rect = bar.getBoundingClientRect();
		seekTo(Math.min(1, Math.max(0, (event.clientX - rect.left) / rect.width)));
	}

	function jumpToWord(word: Word) {
		seekTo(duration ? word.startMs / duration : 0);
		audio?.play();
	}

	function onDrop(event: DragEvent) {
		dragging = false;
		const file = event.dataTransfer?.files?.[0];
		if (file) load(file);
	}

	function onPick(event: Event) {
		const file = (event.currentTarget as HTMLInputElement).files?.[0];
		if (file) load(file);
	}

	// The Fullscreen API reports its own state (Esc, F11, a second tab going
	// fullscreen) independently of who asked for it, so this listens rather
	// than trusting the click handler to be the only way `fullscreen` changes.
	$effect(() => {
		const onChange = () => (fullscreen = document.fullscreenElement === stageEl);
		document.addEventListener('fullscreenchange', onChange);
		return () => document.removeEventListener('fullscreenchange', onChange);
	});

	async function toggleFullscreen() {
		if (!stageEl) return;
		try {
			if (document.fullscreenElement) await document.exitFullscreen();
			else await stageEl.requestFullscreen();
		} catch {
			// A user gesture requirement or a platform without the API: the button
			// simply does nothing rather than throwing into the console.
		}
	}

	const SEEK_STEP_MS = 5000;

	function onKey(event: KeyboardEvent) {
		const tag = (event.target as HTMLElement)?.tagName;
		if (tag === 'INPUT') return;
		if (event.key === ' ') {
			// A focused button already has its own Space activation (play, jump
			// to a word, toggle fullscreen); running toggle() as well would
			// double it. Arrow keys have no such native behaviour on a <button>,
			// so they are not guarded the same way — that guard is what made
			// scrubbing silently stop working after clicking anything.
			if (tag === 'BUTTON') return;
			event.preventDefault();
			toggle();
			return;
		}
		if (event.key === 'ArrowRight') {
			event.preventDefault();
			seekBy(SEEK_STEP_MS);
		} else if (event.key === 'ArrowLeft') {
			event.preventDefault();
			seekBy(-SEEK_STEP_MS);
		} else if (
			event.key.toLowerCase() === 'f' &&
			!event.ctrlKey &&
			!event.metaKey &&
			!event.altKey
		) {
			// Plain f, not Ctrl/Cmd+F: that combination is the browser's own
			// find-on-page shortcut and must reach it untouched.
			event.preventDefault();
			toggleFullscreen();
		}
	}

	const clock = (ms: number) => {
		const total = Math.max(0, Math.floor(ms / 1000));
		return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, '0')}`;
	};
</script>

<svelte:head>
	<title>Karaoke demo — synchronized lyrics in one audio file</title>
	<meta
		name="description"
		content="The Element Song by Tom Lehrer with word-timed lyrics embedded in a single Ogg Opus file, read and played in the browser."
	/>
</svelte:head>

<svelte:window on:keydown={onKey} />

<div class="shell wrap">
	<p class="eyebrow eyebrow--plain">Karaoke demo</p>
	<h1>The Element Song by Tom Lehrer, with its words, in a single <code>.ogg</code> file.</h1>
	<p class="lede">
		The tags that carry a meeting transcript carry lyrics with word-level timestamps just as well.
		Any player plays the song; a player that reads the tags shows the words in time with it.
	</p>
</div>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div
	class="stage"
	class:dragging
	class:is-fullscreen={fullscreen}
	bind:this={stageEl}
	ondragover={(e) => {
		e.preventDefault();
		dragging = true;
	}}
	ondragleave={() => (dragging = false)}
	ondrop={(e) => {
		e.preventDefault();
		onDrop(e);
	}}
>
	<div class="stage__in">
		{#if loading}
			<p class="msg">Reading the file…</p>
		{:else if error}
			<p class="msg msg--bad">{error}</p>
		{:else if stage}
			<div class="rows">
				<p class="context context--before">
					{#each stage.before as word, i (word.startMs + ':' + i)}
						<button class="ctx" data-near={stage.before.length - i} onclick={() => jumpToWord(word)}>
							{word.text}
						</button>
					{/each}
				</p>

				<button
					class="now"
					class:is-sung={cursor.active}
					onclick={() => jumpToWord(stage.current)}
					title={`${clock(stage.current.startMs)} · ${speakerLabel.get(stage.current.speaker) ?? stage.current.speaker}`}
				>
					{stage.current.text}
				</button>

				<p class="context context--after">
					{#each stage.after as word, i (word.startMs + ':' + i)}
						<button class="ctx" data-near={i + 1} onclick={() => jumpToWord(word)}>
							{word.text}
						</button>
					{/each}
				</p>
			</div>
			{#if (result?.manifest?.speakers?.length ?? 0) > 1}
				<p class="who">
					{speakerLabel.get(timeline[cursor.index]?.speaker ?? '') ?? ''}
				</p>
			{/if}
		{:else}
			<p class="msg">No words to show.</p>
		{/if}
	</div>

	<div class="transport">
		<button class="play" onclick={toggle} aria-label={playing ? 'Pause' : 'Play'}>
			{#if playing}❚❚{:else}▶{/if}
		</button>
		<span class="t">{clock(timeMs)}</span>
		<!-- Arrow keys are handled by the page-level listener (svelte:window),
		     which fires for a keydown here too since it bubbles. A second
		     handler on this element would double-step when it has focus. -->
		<div
			class="bar"
			role="slider"
			tabindex="0"
			aria-label="Seek"
			aria-valuemin={0}
			aria-valuemax={100}
			aria-valuenow={Math.round(progress * 100)}
			onclick={onScrub}
		>
			<div class="bar__fill" style="width: {progress * 100}%"></div>
		</div>
		<span class="t">{clock(duration)}</span>
		<button
			class="iconbtn"
			onclick={toggleFullscreen}
			aria-label={fullscreen ? 'Exit fullscreen' : 'Fullscreen'}
			title={fullscreen ? 'Exit fullscreen' : 'Fullscreen'}
		>
			{#if fullscreen}
				<svg viewBox="0 0 20 20" width="15" height="15" aria-hidden="true">
					<path
						fill="none"
						stroke="currentColor"
						stroke-width="1.6"
						stroke-linecap="round"
						stroke-linejoin="round"
						d="M8 3v3.5A1.5 1.5 0 0 1 6.5 8H3M12 3v3.5A1.5 1.5 0 0 0 13.5 8H17M8 17v-3.5A1.5 1.5 0 0 0 6.5 12H3M12 17v-3.5a1.5 1.5 0 0 1 1.5-1.5H17"
					/>
				</svg>
			{:else}
				<svg viewBox="0 0 20 20" width="15" height="15" aria-hidden="true">
					<path
						fill="none"
						stroke="currentColor"
						stroke-width="1.6"
						stroke-linecap="round"
						stroke-linejoin="round"
						d="M3 7V4.5A1.5 1.5 0 0 1 4.5 3H7M13 3h2.5A1.5 1.5 0 0 1 17 4.5V7M17 13v2.5a1.5 1.5 0 0 1-1.5 1.5H13M7 17H4.5A1.5 1.5 0 0 1 3 15.5V13"
					/>
				</svg>
			{/if}
		</button>
	</div>

	<audio
		bind:this={audio}
		src={objectUrl}
		onplay={() => (playing = true)}
		onpause={() => (playing = false)}
		onended={() => (playing = false)}
		ontimeupdate={() => audio && !playing && (timeMs = audio.currentTime * 1000)}
		onloadedmetadata={() => {
			const d = audio?.duration ?? 0;
			// Ogg without a seek table can report Infinity until it has buffered.
			duration = Number.isFinite(d) && d > 0 ? d * 1000 : (result?.manifest?.audio?.durationMs as number) || 0;
		}}
	></audio>
</div>

<div class="shell wrap wrap--after">
	<div class="meta meta--single">
		<div>
			<p class="eyebrow eyebrow--plain">Playing</p>
			<p class="m">
				<strong>{result?.manifest?.meeting?.title ?? sourceName}</strong><br />
				<span class="dim">{sourceName}</span>
			</p>
		</div>
	</div>

	<div class="load">
		<label class="btn">
			Open another file
			<input type="file" accept=".opus,audio/ogg" onchange={onPick} />
		</label>
		<button class="btn" onclick={() => load(DEMO)}>Back to the demo</button>
		<span class="dim">or drop a <code>.opus</code> on the stage. It never leaves the browser.</span>
	</div>
</div>

<style>
	.wrap {
		padding-block: 3.5rem 1.5rem;
	}
	.wrap--after {
		padding-block: 2rem 4rem;
	}
	h1 {
		margin: 1.2rem 0 1.4rem;
		/* This is a sentence of copy, not a short headline, so it wants the
		   ordinary reading measure rather than a narrow one. */
		max-width: var(--col);
	}

	/* --- the stage ---------------------------------------------------------- */
	.stage {
		position: relative;
		border-block: 1px solid var(--rule);
		background:
			radial-gradient(120% 90% at 50% 0%, var(--bg-raise) 0%, transparent 70%),
			var(--bg);
		padding: clamp(1.5rem, 4vw, 3rem) 0 0;
	}
	.stage.dragging {
		outline: 2px dashed var(--blue);
		outline-offset: -8px;
	}
	/* Fullscreen shows only this element's subtree at viewport size, so the
	   words get to use the height a nav bar and footer would otherwise take. */
	.stage.is-fullscreen {
		/* The UA's own :fullscreen stylesheet is supposed to pin this element to
		   the viewport, but it is a normal-priority rule, not an !important one,
		   and how faithfully it is applied varies by browser. Setting the
		   positioning explicitly, rather than trusting that, is what actually
		   keeps the transport bar on screen instead of pushed past the fold. */
		position: fixed;
		inset: 0;
		display: flex;
		flex-direction: column;
		justify-content: center;
		height: 100dvh;
		width: 100vw;
	}
	.stage.is-fullscreen .stage__in {
		flex: 1;
		min-height: 0;
	}
	.stage.is-fullscreen .now {
		font-size: clamp(2.4rem, 1rem + 9vh, 7rem);
	}
	.stage.is-fullscreen .ctx {
		font-size: clamp(1rem, 0.6rem + 2vh, 1.6rem);
	}
	.stage__in {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: clamp(190px, 34vh, 340px);
		padding-inline: var(--pad);
		text-align: center;
	}

	.rows {
		display: grid;
		/* Fixed row heights: the context rows must not resize the stage as words
		   of different lengths pass through them. */
		grid-template-rows: 2.2em minmax(1.3em, auto) 2.2em;
		align-items: center;
		justify-items: center;
		gap: 0.4rem;
		width: 100%;
		max-width: 46ch;
	}

	.context {
		display: flex;
		flex-wrap: nowrap;
		align-items: baseline;
		justify-content: center;
		gap: 0 0.45em;
		margin: 0;
		overflow: hidden;
		max-width: 100%;
	}
	.context--before {
		align-self: end;
	}
	.context--after {
		align-self: start;
	}

	.ctx,
	.now {
		appearance: none;
		background: none;
		border: 0;
		padding: 0;
		font-family: var(--mono);
		cursor: pointer;
		white-space: nowrap;
		transition:
			color 140ms ease,
			opacity 140ms ease;
	}

	.ctx {
		font-size: clamp(0.85rem, 0.75rem + 0.5vw, 1.05rem);
		line-height: 1.5;
		color: var(--fg-4);
	}
	/* Fade with distance from the word being sung, in both directions. */
	.ctx[data-near='2'] {
		opacity: 0.7;
	}
	.ctx[data-near='3'] {
		opacity: 0.45;
	}
	.ctx[data-near='4'] {
		opacity: 0.25;
	}

	.now {
		font-size: clamp(1.8rem, 1.1rem + 3.6vw, 3.6rem);
		font-weight: 600;
		letter-spacing: -0.01em;
		line-height: 1.15;
		/* Between words the last one stays up, but stops claiming to be sung. */
		color: var(--fg-3);
	}
	.now.is-sung {
		color: var(--blue);
	}

	.ctx:focus-visible,
	.now:focus-visible {
		outline: 1px solid var(--blue);
		outline-offset: 3px;
	}

	.who {
		margin: 1.2rem 0 0;
		font-size: 11px;
		letter-spacing: 0.14em;
		text-transform: uppercase;
		color: var(--fg-4);
	}
	.msg {
		color: var(--fg-3);
		margin: 0;
	}
	.msg--bad {
		color: var(--red);
	}

	/* --- transport ---------------------------------------------------------- */
	.transport {
		display: flex;
		align-items: center;
		gap: 0.9rem;
		max-width: var(--shell);
		margin: 0 auto;
		padding: 1.2rem var(--pad) 1.4rem;
	}
	.play {
		flex: none;
		width: 2.4rem;
		height: 2.4rem;
		border: 1px solid var(--rule-hi);
		border-radius: 50%;
		background: none;
		color: var(--fg-2);
		font-size: 12px;
		cursor: pointer;
	}
	.play:hover {
		border-color: var(--blue);
		color: var(--blue);
	}
	.iconbtn {
		flex: none;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 2.4rem;
		height: 2.4rem;
		border: 1px solid var(--rule-hi);
		border-radius: 50%;
		background: none;
		color: var(--fg-2);
		cursor: pointer;
	}
	.iconbtn:hover {
		border-color: var(--blue);
		color: var(--blue);
	}
	.iconbtn:focus-visible {
		outline: 1px solid var(--blue);
		outline-offset: 3px;
	}
	.t {
		flex: none;
		font-family: var(--mono);
		font-size: 12px;
		color: var(--fg-4);
		font-variant-numeric: tabular-nums;
	}
	.bar {
		flex: 1;
		height: 3px;
		background: var(--rule);
		cursor: pointer;
	}
	.bar__fill {
		height: 100%;
		background: var(--blue);
	}
	.bar:focus-visible {
		outline: 1px solid var(--blue);
		outline-offset: 4px;
	}

	/* --- below ------------------------------------------------------------- */
	.meta {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		gap: 1.5rem;
		margin-bottom: 2rem;
	}
	/* One block left (what's playing): a 3-column track would strand it in a
	   narrow third of the row with dead space alongside. */
	.meta--single {
		grid-template-columns: minmax(0, 1fr);
		max-width: 32ch;
	}
	@media (max-width: 700px) {
		.meta {
			grid-template-columns: minmax(0, 1fr);
		}
	}
	.m {
		margin: 0.6rem 0 0;
		font-size: 13px;
		line-height: 1.6;
	}
	.dim {
		color: var(--fg-4);
	}
	.load {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.6rem;
		font-size: 13px;
	}
	.btn {
		display: inline-flex;
		align-items: center;
		border: 1px solid var(--rule);
		padding: 0.45rem 0.8rem;
		font-size: 12px;
		background: none;
		color: var(--fg-2);
		cursor: pointer;
	}
	.btn:hover {
		border-color: var(--blue);
		color: var(--blue);
	}
	.btn input {
		display: none;
	}
</style>
