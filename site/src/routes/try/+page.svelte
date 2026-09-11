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
	<title>Open a Cassini file — audio and transcript in your browser</title>
	<meta
		name="description"
		content="Find a passage in a transcript and listen to check what was actually said. Try a sample meeting or open your own Cassini file. Local files stay in your browser."
	/>
</svelte:head>

<div class="shell page-intro">
	<p class="eyebrow eyebrow--plain">Open a recording</p>
	<h1>Find the words.<br />Hear what was said.</h1>
	<p class="lede">
		Use the transcript to find a passage, then listen to check what was actually said.
		Select a word to move to that moment and press Play. Try the example below or open your own file.
	</p>
	<p class="reader-context">This player opens text already stored in the audio file.
		It does not transcribe recordings. <a href="{base}/using/">How the format works →</a></p>
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
				{typeof source === 'string' ? 'Example recording' : 'Your file'}
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
			Courtesy NASA/JPL-Caltech · September 15, 2017. The final Cassini mission-control calls,
			with a transcript reconciled from multiple models and JPL captions. Uncertain speech is marked;
			two speakers’ names remain unconfirmed.
			<span class="sample-links">
				<a href="https://www.jpl.nasa.gov/videos/final-moments-in-cassini-mission-control/">Original video →</a>
				<a href="{base}/demo/README.md">Sources & transcription notes →</a>
			</span>
		</p>{/if}

	<div class="next">
		<div>
			<p class="eyebrow eyebrow--plain">Take it with you</p>
			<h2>The download is the whole recording.</h2>
			<p>Save the example and open that copy here. The recording travels with the words, so the
				person you send it to can listen and check too. An ordinary Opus player can play the audio;
				a Cassini reader also shows the transcript.</p>
			<a class="button" href="{base}/using/#what-the-recipient-needs">Using and sharing a file →</a>
		</div>
		<div>
			<p class="eyebrow eyebrow--plain">Try it with your own tools</p>
			<h2>Read the data, or create a file.</h2>
			<p>
				Our guides use standalone readers and a producer to work with existing audio and timed
				words. They also explain how to check your result. The data reader is CC0; this
				transcript interface is a separate AGPL-3.0 component.
			</p>
			<a class="button" href="{base}/build/">Choose an implementation path →</a>
		</div>
	</div>
	<p class="sample-note">Another experiment with the same format:
		<a href="{base}/demo/">a song with synchronized lyrics →</a></p>
</div>

<style>
	.reader-page {
		max-width: 1120px;
	}
	.reader-context {
		font-size: 14px;
		max-width: 75ch;
		margin-bottom: 0;
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
