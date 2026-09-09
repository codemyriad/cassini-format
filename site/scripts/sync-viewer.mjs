/** Keep the published Cassini component and its pure transcript model pinned. */
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = fileURLToPath(new URL('../src/lib/vendor/cassini-viewer/', import.meta.url));
const lockPath = path.join(root, 'upstream.json');
const lock = JSON.parse(await readFile(lockPath, 'utf8'));
const args = process.argv.slice(2);
const hash = (data) => createHash('sha256').update(data).digest('hex');

// These opt-in embedding fixes preserve Cassini's turn/interjection model.
// Exact replacements intentionally fail when an upstream update needs review.
function embedPatch(source) {
	const replacements = [
		['  export let bundled = false;', `  export let bundled = false;
  // Format-site embedding: keep shortcuts and follow scrolling inside this panel.
  export let contained = false;`],
		['    enriched: MeetingCatalogEntry;', '    enriched: MeetingCatalogEntry;\n    playbackerror: string;'],
		['  <main class="flex flex-col gap-3.5 m-4 min-[981px]:m-8">', '  <svelte:element this={contained ? "div" : "main"} data-transcript-content class="flex flex-col gap-3.5 m-4 min-[981px]:m-8">'],
		['  </main>', '  </svelte:element>'],
		['      void audioEl.play();', `      void audioEl.play().catch(() => {
        dispatch("playbackerror", "Playback could not start. Try again or download the audio file.");
      });`],
		['    element?.scrollIntoView({ behavior, block: "center" });', `    if (contained && element) {
      const pane = viewRootEl?.firstElementChild as HTMLElement | undefined;
      if (pane) {
        const bounds = pane.getBoundingClientRect();
        const position = element.getBoundingClientRect();
        if (position.top < bounds.top + 24 || position.bottom > bounds.bottom - 24) {
          pane.scrollTo({ top: pane.scrollTop + position.top - bounds.top - bounds.height / 3, behavior });
        }
      }
      return;
    }
    element?.scrollIntoView({ behavior, block: "center" });`],
		['  function handleWindowKeydown(event: KeyboardEvent) {', `  function handleWindowKeydown(event: KeyboardEvent) {
    if (contained && (!viewRootEl || !event.composedPath().includes(viewRootEl))) return;`],
		['            on:durationchange={handleDurationChange}', `            on:error={() => dispatch("playbackerror", "This browser could not play the audio file. You can download it to listen in an Opus player.")}
            on:durationchange={handleDurationChange}`]
	];
	for (const [before, after] of replacements) {
		if (source.split(before).length !== 2) throw new Error(`Upstream changed at embedding patch: ${before}`);
		source = source.replace(before, after);
	}
	return source;
}

// Narrow optional values for the site's TypeScript 6 checker. These are
// type-only changes; they preserve the upstream portable projection exactly.
function portableTypePatch(source) {
	const replacements = [
		['    ref.rawBytes < 0 ||', '    ref.rawBytes! < 0 ||'],
		['    ref.gzipBytes < 0 ||', '    ref.gzipBytes! < 0 ||'],
		['speakerLabels.get(block.speaker) || "Unknown speaker"', 'speakerLabels.get(block.speaker!) || "Unknown speaker"'],
		['function tokenHasTiming(token: DisplayTranscriptV1["blocks"][number]["tokens"][number] | null | undefined): boolean {\n  return Boolean(token)', 'function tokenHasTiming(token: DisplayTranscriptV1["blocks"][number]["tokens"][number] | null | undefined): token is DisplayTranscriptV1["blocks"][number]["tokens"][number] {\n  return !!token'],
		['new Blob([bytes])', 'new Blob([bytes as Uint8Array<ArrayBuffer>])'],
		['sourceSegmentIds.map((segmentId) => segmentById.get(segmentId)).filter(Boolean)', 'sourceSegmentIds.map((segmentId) => segmentById.get(segmentId)).filter((segment): segment is TranscriptWordsV1["segments"][number] => Boolean(segment))']
	];
	for (const [before, after] of replacements) {
		if (source.split(before).length !== 2) throw new Error(`Upstream changed at type patch: ${before}`);
		source = source.replace(before, after);
	}
	return source;
}

if (args.includes('--check')) {
	for (const [file, entry] of Object.entries(lock.files)) {
		const bytes = await readFile(path.join(root, file));
		if (hash(bytes) !== (entry.patchedSha256 ?? entry.sha256)) {
			throw new Error(`Vendored ${file} differs from the pinned Cassini component. Re-sync or review the embedding patch.`);
		}
	}
	console.log(`Cassini viewer source matches ${lock.commit.slice(0, 12)}`);
} else {
	const from = args.indexOf('--from');
	if (from < 0 || !args[from + 1]) throw new Error('Usage: node scripts/sync-viewer.mjs --from /path/to/gocassini [--ref COMMIT]');
	const repo = path.resolve(args[from + 1]);
	const ref = args.indexOf('--ref');
	const commit = execFileSync('git', ['-C', repo, 'rev-parse', ref >= 0 ? args[ref + 1] : lock.commit], { encoding: 'utf8' }).trim();
	for (const [file, entry] of Object.entries(lock.files)) {
		const bytes = execFileSync('git', ['-C', repo, 'show', `${commit}:${entry.source}`]);
		entry.sha256 = hash(bytes);
		const patch = file === 'src/components/MeetingView.svelte' ? embedPatch : file === 'src/viewer/portable.ts' ? portableTypePatch : null;
		const output = patch ? Buffer.from(patch(bytes.toString())) : bytes;
		if (patch) entry.patchedSha256 = hash(output);
		await mkdir(path.dirname(path.join(root, file)), { recursive: true });
		await writeFile(path.join(root, file), output);
	}
	const readmePath = path.join(root, 'README.md');
	const readme = await readFile(readmePath, 'utf8').catch(() => '');
	if (readme) await writeFile(readmePath, readme.replaceAll(lock.commit, commit));
	lock.commit = commit;
	await writeFile(lockPath, `${JSON.stringify(lock, null, 2)}\n`);
	console.log(`Synced Cassini viewer ${commit}. Run npm run gen:viewer-css and npm run test:viewer.`);
}
