<script lang="ts">
	import { base } from '$app/paths';
	import { untrack } from 'svelte';
	import Player from '$lib/components/Player.svelte';

	let { data } = $props();

	const example = $derived(`${base}/demo/${data.filename}`);
	let source = $state<string | File>(untrack(() => example));
	let fileInput: HTMLInputElement;
	let dragging = $state(false);
	let fileError = $state('');
	const name = $derived(typeof source === 'string' ? data.title : source.name);

	function openFile(file?: File) {
		if (!file) return;
		fileError = '';
		if (
			!/\.(opus|ogg)$/i.test(file.name) &&
			!['audio/ogg', 'audio/opus', 'application/ogg'].includes(file.type)
		) {
			fileError = 'Choose an Ogg Opus file (.opus or .ogg).';
			return;
		}
		source = file;
	}
</script>

<svelte:head>
	<title>Try a Cassini file — audio and transcript in your browser</title>
	<meta
		name="description"
		content="Play a sample meeting or open your own Cassini .opus file. Follow the highlighted words and click any word to seek. Local files stay in your browser."
	/>
</svelte:head>

<div class="shell page-intro">
	<p class="eyebrow eyebrow--plain">Try the format</p>
	<h1>Open the file.<br />Find the words.</h1>
	<p class="lede">
		Listen to the example below, or open a recording of your own. Words highlight as they play.
		Click any word to jump to that moment, including words in an overlapping reply.
	</p>
</div>

<div class="shell reader-page">
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div
		class="file-picker"
		class:dragging
		ondragover={(event) => {
			event.preventDefault();
			dragging = true;
		}}
		ondragleave={(event) => {
			if (!event.currentTarget.contains(event.relatedTarget as Node)) dragging = false;
		}}
		ondrop={(event) => {
			event.preventDefault();
			dragging = false;
			openFile(event.dataTransfer?.files[0]);
		}}
	>
		<div>
			<h2>Bring your own recording</h2>
			<p>
				Drop an <code>.opus</code> or <code>.ogg</code> file here. Local files stay in your browser.
			</p>
		</div>
		<button class="button button--primary" onclick={() => fileInput.click()}
			>Open a file <span aria-hidden="true">↑</span></button
		>
		<input
			bind:this={fileInput}
			type="file"
			accept=".opus,.ogg,audio/ogg,audio/opus"
			aria-label="Choose an audio file"
			onchange={(event) => {
				openFile(event.currentTarget.files?.[0]);
				event.currentTarget.value = '';
			}}
		/>
	</div>
	{#if fileError}<p class="file-error" role="alert">{fileError}</p>{/if}

	<div class="reader-heading">
		<div>
			<p class="eyebrow eyebrow--plain">
				{typeof source === 'string' ? 'Example meeting' : 'Your file'}
			</p>
			<h2>{name}</h2>
		</div>
		{#if typeof source !== 'string'}<button
				class="button"
				onclick={() => {
					source = example;
					fileError = '';
				}}>Back to the example</button
			>
		{:else}<a class="text-link" href={example} download>Download example ↓</a>{/if}
	</div>
	<Player src={source} fallbackTitle={name} />
	{#if typeof source === 'string'}<p class="sample-note">
			A fictional planning call voiced with ElevenLabs v3, with a separate audio track for each
			speaker. Cassini processed those tracks into the recording and word-timed transcript above.
			Four brief replies overlap the main speaker.
			<span class="sample-links">
				<a href="{base}/demo/repair-cafe.multitrack.mkv" download>Download source tracks (.mkv) ↓</a
				>
				<a href="{base}/demo/README.md">How it was made →</a>
			</span>
		</p>{/if}

	<div class="next">
		<div>
			<p class="eyebrow eyebrow--plain">The same format, set to music</p>
			<h2>A song can carry its lyrics, too.</h2>
			<p>Try the karaoke view of Tom Lehrer’s Element Song, with words highlighted as it plays.</p>
			<a class="button" href="{base}/demo/">Open the karaoke demo →</a>
		</div>
		<div>
			<p class="eyebrow eyebrow--plain">Make it your own</p>
			<h2>Build a reader like this one.</h2>
			<p>
				The standalone browser reader is CC0 and uses standard web APIs with no runtime
				dependencies. The transcript interface shown here is Cassini’s own component, licensed under
				AGPL-3.0.
			</p>
			<a class="button" href="{base}/consume/">Read a file in code →</a>
		</div>
	</div>
</div>

<style>
	.reader-page {
		max-width: 1120px;
	}
	.file-picker {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1.5rem;
		border: 1px dashed var(--rule-hi);
		border-radius: 7px;
		padding: 1.5rem;
		background: var(--bg-raise);
	}
	.file-picker.dragging {
		border-color: var(--blue);
		background: var(--blue-wash);
	}
	.file-picker h2 {
		font-size: 19px;
		margin-bottom: 0.5rem;
	}
	.file-picker p {
		margin: 0;
		font-size: 14px;
	}
	.file-picker .button {
		flex: none;
	}
	.file-picker input {
		display: none;
	}
	.file-error {
		margin-top: 0.75rem;
		color: var(--red);
		font-size: 14px;
	}
	.reader-heading {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1.5rem;
		margin-block: 3rem 1.2rem;
	}
	.reader-heading h2 {
		font-size: 24px;
		margin-top: 0.75rem;
		overflow-wrap: anywhere;
	}
	.reader-heading > a,
	.reader-heading > button {
		flex: none;
	}
	.sample-note {
		font-size: 13px;
		margin-top: 1rem;
		max-width: 90ch;
		color: var(--fg-4);
	}
	.sample-links {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem 1.25rem;
		margin-top: 0.5rem;
	}
	.next {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 3rem;
		border-top: 1px solid var(--rule);
		margin-top: 4rem;
		padding-top: 2.5rem;
	}
	.next h2 {
		font-size: 24px;
		margin-block: 1rem 0.75rem;
	}
	.next p:not(.eyebrow) {
		font-size: 15px;
	}
	@media (max-width: 650px) {
		.file-picker,
		.reader-heading {
			flex-direction: column;
			align-items: flex-start;
		}
		.next {
			grid-template-columns: minmax(0, 1fr);
		}
	}
</style>
