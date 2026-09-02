<script lang="ts">
	import { untrack } from 'svelte';
	import { readCassini, toTurns, type ReadResult, type Word } from '$lib/reader/cassini';

	let { src, fallbackTitle = '' }: { src: string; fallbackTitle?: string } = $props();

	type Step = { label: string; state: 'wait' | 'run' | 'ok' | 'fail'; detail?: string };

	let steps = $state<Step[]>([
		{ label: 'fetch the .opus', state: 'wait' },
		{ label: 'walk the Ogg pages, find OpusTags', state: 'wait' },
		{ label: 'reassemble CASSINI_PAYLOAD_000..N', state: 'wait' },
		{ label: 'gunzip, parse, check SHA-256', state: 'wait' },
		{ label: 'resolve the default transcript', state: 'wait' }
	]);
	let result = $state<ReadResult | null>(null);
	let error = $state('');
	let audio = $state<HTMLAudioElement | null>(null);
	let timeMs = $state(0);
	let playing = $state(false);
	let duration = $state(0);
	let follow = $state(true);
	let objectUrl = $state('');

	// untrack matters here: mark() READS steps, and it is called from inside the
	// $effect that loads the file. Without it the read registers as a dependency,
	// the write re-triggers the effect, and the browser downloads the file forever.
	const mark = (i: number, state: Step['state'], detail?: string) => {
		untrack(() => {
			steps[i] = { ...steps[i], state, detail };
		});
	};

	$effect(() => {
		let cancelled = false;
		(async () => {
			try {
				mark(0, 'run');
				const response = await fetch(src);
				if (!response.ok) throw new Error(`${response.status} fetching the file`);
				const bytes = await response.blob();
				const buf = await bytes.arrayBuffer();
				if (cancelled) return;
				// Play the bytes we already have rather than making the browser
				// download the same 1.3 MB a second time for the <audio> element.
				objectUrl = URL.createObjectURL(bytes);
				mark(0, 'ok', `${(buf.byteLength / 1024 / 1024).toFixed(2)} MB`);

				mark(1, 'run');
				const read = await readCassini(buf);
				if (cancelled) return;
				mark(1, 'ok', `${read.tags.size} comments`);
				mark(2, 'ok', `${read.tags.get('CASSINI_PAYLOAD_CHUNK_COUNT')?.[0] ?? '?'} chunk(s)`);
				mark(
					3,
					read.verified.manifest === false ? 'fail' : 'ok',
					read.verified.manifest ? 'manifest digest matches' : 'unverified'
				);
				mark(
					4,
					read.transcript ? 'ok' : 'fail',
					read.transcript
						? `${read.transcript.entry.id} — ${read.transcript.words.length} words${
								read.verified.transcript ? ', digest matches' : ''
							}`
						: read.unavailable
							? `${read.unavailable.entry.id} could not be loaded`
							: 'no transcript recovered'
				);
				result = read;
			} catch (e) {
				if (cancelled) return;
				error = e instanceof Error ? e.message : String(e);
				const i = untrack(() => steps.findIndex((s) => s.state === 'run'));
				if (i >= 0) mark(i, 'fail');
				// The transcript is gone but the audio is not. Fall back to letting
				// the browser fetch and play it the ordinary way, which is exactly
				// what the format promises when a reader gives up.
				if (!objectUrl) objectUrl = src;
			}
		})();
		return () => {
			cancelled = true;
			if (objectUrl) URL.revokeObjectURL(objectUrl);
		};
	});

	const turns = $derived(
		result?.transcript && result.manifest
			? toTurns(result.transcript.words, result.manifest.speakers)
			: []
	);
	const speakerIndex = $derived(
		new Map((result?.manifest?.speakers ?? []).map((s, i) => [s.id, i]))
	);

	// File order is speaker-turn order, not time order: across a speaker change
	// startMs goes backwards. Rendering keeps file order; lookup by time needs
	// its own index, sorted by startMs and holding the file position.
	const byTime = $derived.by(() => {
		const words = result?.transcript?.words ?? [];
		return words.map((w, i) => ({ startMs: w.startMs, i })).sort((a, b) => a.startMs - b.startMs);
	});

	const activeWord = $derived.by(() => {
		const words = result?.transcript?.words;
		if (!words || !byTime.length) return -1;
		let lo = 0;
		let hi = byTime.length - 1;
		let found = -1;
		while (lo <= hi) {
			const mid = (lo + hi) >> 1;
			if (byTime[mid].startMs <= timeMs) {
				found = mid;
				lo = mid + 1;
			} else hi = mid - 1;
		}
		if (found < 0) return -1;
		// Several words can start before now; take the one still being said,
		// or the latest to start if none is.
		let pick = byTime[found].i;
		for (let k = found; k >= 0 && byTime[found].startMs - byTime[k].startMs < 3000; k--) {
			const w = words[byTime[k].i];
			if (w.startMs <= timeMs && timeMs <= w.endMs) {
				pick = byTime[k].i;
				break;
			}
		}
		if (timeMs > words[pick].endMs + 900) return -1;
		return pick;
	});

	const stateLine = $derived.by(() => {
		if (!result) return '';
		switch (result.state) {
			case 'unverified':
				return 'unverified: the manifest and transcript digests match; the audio digest is not checked in the browser.';
			case 'invalid-cassini-metadata':
				return 'invalid-cassini-metadata: the metadata could not be reconstructed. The recording still plays.';
			case 'unknown-cassini-format':
				return 'unknown-cassini-format: metadata in a version this reader does not implement. The recording still plays.';
			default:
				return result.state;
		}
	});

	function seekTo(ms: number) {
		if (!audio) return;
		audio.currentTime = ms / 1000;
		timeMs = ms;
		if (!playing) audio.play();
	}

	function toggle() {
		if (!audio) return;
		playing ? audio.pause() : audio.play();
	}

	const clock = (ms: number) =>
		`${Math.floor(ms / 60000)}:${String(Math.floor((ms % 60000) / 1000)).padStart(2, '0')}`;

	// Keep the active turn in view, unless the reader has scrolled away.
	let scroller = $state<HTMLElement | null>(null);
	$effect(() => {
		if (!follow || activeWord < 0 || !scroller) return;
		const el = scroller.querySelector<HTMLElement>('[data-active="true"]');
		if (!el) return;
		const box = scroller.getBoundingClientRect();
		const spot = el.getBoundingClientRect();
		if (spot.top < box.top + 40 || spot.bottom > box.bottom - 40) {
			scroller.scrollTop += spot.top - box.top - box.height / 3;
		}
	});
</script>

<div class="player">
	<div class="steps">
		{#each steps as step, i (step.label)}
			<div class="step" data-state={step.state}>
				<span class="dot"></span>
				<span class="lab">{step.label}</span>
				{#if step.detail}<span class="det">{step.detail}</span>{/if}
			</div>
		{/each}
	</div>

	{#if error}
		<p class="err">The reader stopped: {error}. The file is still playable as audio.</p>
	{/if}
	{#if result}
		<p class="state" data-state={result.state}>{stateLine}</p>
	{/if}
	{#if result?.warnings.length}
		<ul class="warn">
			{#each result.warnings as warning, i (i)}
				<li>{warning.message}</li>
			{/each}
		</ul>
	{/if}

	<div class="bar">
		<button class="play" type="button" onclick={toggle} aria-label={playing ? 'Pause' : 'Play'}>
			{#if playing}❚❚{:else}▶{/if}
		</button>
		<div
			class="track"
			role="slider"
			tabindex="0"
			aria-label="Seek"
			aria-valuemin={0}
			aria-valuemax={Math.round(duration)}
			aria-valuenow={Math.round(timeMs / 1000)}
			onkeydown={(e) => {
				if (e.key === 'ArrowRight') seekTo(timeMs + 5000);
				if (e.key === 'ArrowLeft') seekTo(Math.max(0, timeMs - 5000));
			}}
			onclick={(e) => {
				const r = (e.currentTarget as HTMLElement).getBoundingClientRect();
				seekTo(((e.clientX - r.left) / r.width) * duration * 1000);
			}}
		>
			<div class="fill" style:width="{duration ? (timeMs / 1000 / duration) * 100 : 0}%"></div>
			{#each turns as turn, i (i)}
				<span
					class="tick"
					style:left="{duration ? (turn.startMs / 1000 / duration) * 100 : 0}%"
					style:--i={speakerIndex.get(turn.speaker) ?? 0}
				></span>
			{/each}
		</div>
		<span class="time">{clock(timeMs)} / {clock(duration * 1000)}</span>
		<label class="follow">
			<input type="checkbox" bind:checked={follow} /> follow
		</label>
	</div>

	<audio
		bind:this={audio}
		src={objectUrl}
		preload="metadata"
		ontimeupdate={(e) => (timeMs = e.currentTarget.currentTime * 1000)}
		onloadedmetadata={(e) => (duration = e.currentTarget.duration)}
		onplay={() => (playing = true)}
		onpause={() => (playing = false)}
	></audio>

	<div class="transcript" bind:this={scroller}>
		{#if result?.manifest}
			{#each turns as turn, ti (ti)}
				{@const live = activeWord >= 0 && turn.words.includes(result.transcript!.words[activeWord])}
				<div class="turn" data-active={live}>
					<button
						class="who"
						type="button"
						style:--i={speakerIndex.get(turn.speaker) ?? 0}
						onclick={() => seekTo(turn.startMs)}
					>
						<span class="t">{clock(turn.startMs)}</span>
						<span class="nm">{turn.label}</span>
					</button>
					<p>
						{#each turn.words as word, wi (wi)}<button
								class="w"
								type="button"
								data-active={result.transcript!.words[activeWord] === word}
								data-low={word.lowConfidenceSpeaker ? 'true' : undefined}
								title={word.lowConfidenceSpeaker
									? `${word.startMs}–${word.endMs} ms, speaker attribution uncertain`
									: `${word.startMs}–${word.endMs} ms`}
								onclick={() => seekTo(word.startMs)}>{word.text}</button
							>{' '}{/each}
					</p>
				</div>
			{/each}
		{:else if !error && !result}
			<p class="loading">decoding {fallbackTitle}…</p>
		{/if}
	</div>
</div>

<style>
	.player {
		border: 1px solid var(--rule);
		background: var(--bg-raise);
	}
	.steps {
		display: grid;
		gap: 0.2rem;
		padding: 0.9rem 1rem;
		border-bottom: 1px solid var(--rule);
		font-size: 12px;
		background: var(--bg);
	}
	.step {
		display: flex;
		align-items: baseline;
		gap: 0.6rem;
		color: var(--fg-5);
	}
	.dot {
		width: 6px;
		height: 6px;
		flex: none;
		border: 1px solid currentColor;
		border-radius: 50%;
		transform: translateY(-1px);
	}
	.step[data-state='run'] {
		color: var(--fg-3);
	}
	.step[data-state='run'] .dot {
		background: var(--fg-3);
		animation: pulse 1s ease-in-out infinite;
	}
	.step[data-state='ok'] {
		color: var(--fg-3);
	}
	.step[data-state='ok'] .dot {
		background: var(--green);
		border-color: var(--green);
	}
	.step[data-state='fail'] {
		color: var(--red);
	}
	.step[data-state='fail'] .dot {
		background: var(--red);
		border-color: var(--red);
	}
	.det {
		color: var(--fg-5);
		margin-left: auto;
		text-align: right;
	}
	@keyframes pulse {
		50% {
			opacity: 0.3;
		}
	}

	.state {
		margin: 0;
		padding: 0.6rem 1rem;
		border-bottom: 1px solid var(--rule);
		color: var(--fg-4);
		font-size: 12px;
		max-width: none;
	}
	.state[data-state='invalid-cassini-metadata'],
	.state[data-state='unknown-cassini-format'] {
		color: var(--amber);
	}
	.warn {
		margin: 0;
		padding: 0.8rem 1rem 0.8rem 2.1rem;
		border-bottom: 1px solid var(--rule);
		color: var(--amber);
		font-size: 12.5px;
	}
	.err {
		margin: 0;
		padding: 0.8rem 1rem;
		border-bottom: 1px solid var(--rule);
		color: var(--red);
		font-size: 12.5px;
		max-width: none;
	}

	.bar {
		display: flex;
		align-items: center;
		gap: 0.9rem;
		padding: 0.75rem 1rem;
		border-bottom: 1px solid var(--rule);
	}
	.play {
		font: inherit;
		font-size: 12px;
		width: 34px;
		height: 30px;
		flex: none;
		border: 1px solid var(--rule);
		background: var(--bg);
		color: var(--fg);
		cursor: pointer;
	}
	.play:hover {
		border-color: var(--blue);
		color: var(--blue);
	}
	.track {
		position: relative;
		flex: 1;
		height: 26px;
		background: var(--bg);
		border: 1px solid var(--rule);
		cursor: pointer;
		overflow: hidden;
	}
	.fill {
		position: absolute;
		inset: 0 auto 0 0;
		background: var(--blue-wash);
		border-right: 1px solid var(--blue);
	}
	.tick {
		position: absolute;
		top: 0;
		bottom: 0;
		width: 2px;
		opacity: 0.5;
		background: hsl(calc(200 + var(--i) * 38) 70% 65%);
	}
	.time {
		font-size: 12px;
		color: var(--fg-4);
		flex: none;
		font-variant-numeric: tabular-nums;
	}
	.follow {
		font-size: 11px;
		color: var(--fg-4);
		display: flex;
		gap: 0.3rem;
		align-items: center;
		flex: none;
		cursor: pointer;
	}

	.transcript {
		max-height: 420px;
		overflow-y: auto;
		padding: 1rem;
		scrollbar-width: thin;
	}
	.loading {
		color: var(--fg-4);
		font-size: 13px;
	}
	.turn {
		display: grid;
		grid-template-columns: 11rem minmax(0, 1fr);
		gap: 1rem;
		padding: 0.5rem 0;
		border-top: 1px solid transparent;
	}
	.turn[data-active='true'] {
		border-top-color: var(--rule);
		background: var(--bg-raise);
	}
	@media (max-width: 720px) {
		.turn {
			grid-template-columns: minmax(0, 1fr);
			gap: 0.15rem;
		}
	}
	.who {
		font: inherit;
		text-align: left;
		background: none;
		border: 0;
		padding: 0;
		cursor: pointer;
		display: flex;
		gap: 0.5rem;
		align-items: baseline;
		height: fit-content;
	}
	.who .t {
		color: var(--fg-5);
		font-size: 11.5px;
		font-variant-numeric: tabular-nums;
	}
	.who .nm {
		color: hsl(calc(200 + var(--i) * 38) 60% 72%);
		font-size: 12.5px;
		font-weight: 500;
	}
	:global(:root[data-theme='light']) .who .nm {
		color: hsl(calc(200 + var(--i) * 38) 55% 34%);
	}
	.turn p {
		margin: 0;
		font-size: 13.5px;
		color: var(--fg-2);
		max-width: 68ch;
	}
	.w {
		font: inherit;
		background: none;
		border: 0;
		padding: 0;
		margin: 0;
		color: inherit;
		cursor: pointer;
		border-bottom: 1px solid transparent;
	}
	.w:hover {
		border-bottom-color: var(--rule-hi);
	}
	.w[data-active='true'] {
		background: var(--blue-wash);
		color: var(--fg);
		box-shadow: 0 1px 0 var(--blue);
	}
	/* Words the attribution stage was not confident about. Still transcript
	   content: marked, not hidden. */
	.w[data-low='true'] {
		border-bottom: 1px dashed var(--amber-rule);
	}
</style>
