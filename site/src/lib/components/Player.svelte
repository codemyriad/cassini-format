<script lang="ts">
	import { untrack } from 'svelte';
	import { readCassini, type ReadResult } from '$lib/reader/cassini';
	import CassiniView from '$lib/viewer/CassiniView.svelte';
	import { toViewerArtifact } from '$lib/viewer/artifact';

	let {
		src,
		fallbackTitle = '',
		compact = false
	}: { src: string | File; fallbackTitle?: string; compact?: boolean } = $props();

	type Step = { label: string; state: 'wait' | 'run' | 'ok' | 'fail' | 'skip'; detail?: string };

	let steps = $state<Step[]>([
		{ label: 'read the audio file', state: 'wait' },
		{ label: 'walk the Ogg pages, find OpusTags', state: 'wait' },
		{ label: 'reassemble CASSINI_PAYLOAD_000..N', state: 'wait' },
		{ label: 'gunzip, parse, check SHA-256', state: 'wait' },
		{ label: 'resolve the default transcript', state: 'wait' }
	]);
	let result = $state<ReadResult | null>(null);
	let error = $state('');
	let objectUrl = $state('');
	let loading = $state(true);
	let playbackError = $state('');

	// untrack matters here: mark() READS steps, and it is called from inside the
	// $effect that loads the file. Without it the read registers as a dependency,
	// the write re-triggers the effect, and the browser downloads the file forever.
	const mark = (i: number, state: Step['state'], detail?: string) => {
		untrack(() => {
			steps[i] = { ...steps[i], state, detail };
		});
	};

	$effect(() => {
		const source = src;
		let cancelled = false;
		let ownedUrl = '';
		const controller = new AbortController();
		untrack(() => {
			result = null;
			error = '';
			playbackError = '';
			objectUrl = '';
			loading = true;
			steps = steps.map((step) => ({ label: step.label, state: 'wait' }));
		});
		(async () => {
			try {
				mark(0, 'run');
				let bytes: Blob;
				if (source instanceof File) {
					bytes = source;
				} else {
					const response = await fetch(source, { signal: controller.signal });
					if (!response.ok) throw new Error(`${response.status} fetching the file`);
					bytes = await response.blob();
				}
				const buf = await bytes.arrayBuffer();
				if (cancelled) return;
				// Play the bytes we already have rather than making the browser
				// download the audio a second time for the <audio> element.
				ownedUrl = URL.createObjectURL(new Blob([buf], { type: 'audio/ogg' }));
				objectUrl = ownedUrl;
				mark(0, 'ok', `${(buf.byteLength / 1024 / 1024).toFixed(2)} MB`);

				mark(1, 'run');
				const read = await readCassini(buf);
				if (cancelled) return;
				mark(1, 'ok', `${read.tags.size} comments`);
				mark(
					2,
					read.manifest ? 'ok' : read.cassini ? 'fail' : 'skip',
					read.manifest
						? `${read.tags.get('CASSINI_PAYLOAD_CHUNK_COUNT')?.[0] ?? '?'} chunk(s)`
						: 'no readable manifest'
				);
				mark(
					3,
					read.verified.manifest === false ? 'fail' : read.verified.manifest ? 'ok' : 'skip',
					read.verified.manifest
						? 'manifest digest matches'
						: read.verified.manifest === false
							? 'manifest digest mismatch'
							: 'not verified'
				);
				mark(
					4,
					read.transcript ? 'ok' : read.unavailable ? 'fail' : 'skip',
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
				if (!ownedUrl && typeof source === 'string') objectUrl = source;
			} finally {
				if (!cancelled) loading = false;
			}
		})();
		return () => {
			cancelled = true;
			controller.abort();
			if (ownedUrl) URL.revokeObjectURL(ownedUrl);
		};
	});

	const artifact = $derived(
		result?.manifest && result.transcript ? toViewerArtifact(result, objectUrl) : null
	);

	const stateLine = $derived.by(() => {
		if (!result) return '';
		switch (result.state) {
			case 'unverified':
				return 'Unverified · Audio digest not checked in this browser.';
			case 'plain-audio':
				return 'Plain audio · This file has no Cassini transcript. You can still listen.';
			case 'invalid-cassini-metadata':
				return 'invalid-cassini-metadata: the metadata could not be reconstructed. The recording still plays.';
			case 'unknown-cassini-format':
				return 'unknown-cassini-format: metadata in a version this reader does not implement. The recording still plays.';
			default:
				return result.state;
		}
	});
</script>

<div class="player" class:compact aria-label="Audio and transcript player" aria-busy={loading}>
	{#if error}
		<p class="err" role="alert">
			Could not read the transcript: {error}. Audio playback is available if the file is valid
			audio.
		</p>
	{/if}
	{#if playbackError}<p class="err" role="alert">{playbackError}</p>{/if}

	{#if result?.warnings.length}
		<ul class="warn">
			{#each result.warnings as warning, i (i)}
				<li>{warning.message}</li>
			{/each}
		</ul>
	{/if}

	{#if artifact}
		<CassiniView {artifact} {compact} onplaybackerror={(message) => (playbackError = message)} />
	{:else}
		<div class="fallback">
			{#if loading}
				<p class="loading" role="status">Reading {fallbackTitle || 'the recording'}…</p>
			{:else if result}
				<p class="loading">
					{result.state === 'plain-audio'
						? 'No embedded transcript in this file.'
						: 'No word-timed transcript could be loaded from this file.'}
				</p>
			{/if}
			{#if objectUrl}
				<audio
					src={objectUrl}
					controls
					preload="metadata"
					aria-label="Recording playback"
					onerror={() =>
						(playbackError =
							'This file could not be played. Check that it is valid Ogg Opus audio and that your browser supports it.')}
				>
				</audio>
			{/if}
		</div>
	{/if}
	{#if result}
		<p class="state" role="status" data-state={result.state}>{stateLine}</p>
	{/if}
	<details class="diagnostics">
		<summary
			>File details <span
				>{loading ? 'Reading…' : (result?.state ?? 'Could not read metadata')}</span
			></summary
		>
		<div class="steps">
			{#each steps as step, i (step.label)}
				<div class="step" data-state={step.state}>
					<span class="dot"></span>
					<span class="lab">{step.label}</span>
					{#if step.detail}<span class="det">{step.detail}</span>{/if}
				</div>
			{/each}
		</div>
	</details>
</div>

<style>
	.player {
		display: flex;
		flex-direction: column;
		border: 1px solid var(--rule);
		background: var(--bg-raise);
		border-radius: 6px;
		overflow: hidden;
		min-width: 0;
	}
	.compact {
		border: 0;
		border-radius: 0;
		background: transparent;
	}
	.diagnostics {
		border-top: 1px solid var(--rule);
	}
	.diagnostics summary {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		cursor: pointer;
		padding: 0.65rem 1rem;
		font-size: 11px;
		color: var(--fg-4);
	}
	.diagnostics summary span {
		font-family: var(--mono);
		font-size: 10px;
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
		border-block: 1px solid var(--rule);
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

	.fallback {
		padding: 1rem;
	}
	.fallback audio {
		width: 100%;
	}
	.loading {
		color: var(--fg-4);
		font-size: 13px;
	}
	@media (max-width: 560px) {
		.step {
			flex-wrap: wrap;
		}
		.det {
			margin-left: 0;
			text-align: left;
			overflow-wrap: anywhere;
		}
	}
</style>
