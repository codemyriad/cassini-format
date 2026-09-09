import { site } from '$lib/site';
import { origin } from '$lib/origin';
import { listSchemas } from '$lib/docs';
import demo from '$lib/generated/demo.json';

export const prerender = true;
export const trailingSlash = 'never';

/**
 * A short index for anyone pointing a model at this site. The convention is
 * llms.txt for the map and llms-full.txt for the whole thing in one paste.
 */
export async function GET() {
	const schemas = await listSchemas();

	const body = `# ${site.formatName} format

> ${site.description} The container is Ogg, the audio is Opus, the media type is
> audio/ogg. Metadata rides in the OpusTags comment header in two layers: plain
> Vorbis comments, and a gzipped base64url JSON manifest split across numbered
> CASSINI_PAYLOAD_000..N tags. Current wire version: ${site.formatId}.

If you are writing a reader or a producer, take ${origin}/llms-full.txt instead.
It is this whole specification flattened into one document.

## Specification

- [The specification](${origin}/spec/v1/): what a producer writes and a consumer reads today
- [Transcript body, cassini.words.v1](${origin}/spec/words-v1/): one item per word, with a speaker and millisecond offsets
- [Audio digest, exact-opus-audio-v1](${origin}/spec/audio-integrity/): the byte rule that makes a recording's identity survive a tag rewrite

## Guides

- [Try a file](${origin}/try/): play the example or read a local file in the browser
- [Reading a file](${origin}/consume/): the eight steps, and every behaviour a reader has to decide
- [Writing a file](${origin}/produce/): numbered requirements, then conventions
- [Design notes](${origin}/design/): the measurements behind the non-obvious parts
- [Status](${origin}/status/): version 1, published 2026-09-02; what is still open

## Schemas

${schemas.map((s) => `- [${s.title}](${origin}/schema/${s.file})`).join('\n')}

## A playable example

- [${demo.generatedFrom}](${origin}/demo/${demo.generatedFrom}): a valid ${site.formatId} file, ${(demo.bytes / 1024 / 1024).toFixed(2)} MB, ${Object.keys(demo.speakers).length} speakers, ${demo.transcript?.wordCount ?? 0} word-timed items. “${demo.readableTags.TITLE}” is a scripted conversation between fictional volunteers, voiced with Eleven v3 and four overlapping acknowledgments.
- [How it was made](${origin}/demo/README.md)
- The site uses Cassini’s AGPL-3.0 transcript component, with inline interjections, playback highlighting, and seeking from timestamps, passages or brief replies.

## Standalone reference code, all CC0

- [tools/cassini-read.js](${site.repo}/blob/main/tools/cassini-read.js): a browser reader, no dependencies
- [tools/cassini-read-pure.py](${site.repo}/blob/main/tools/cassini-read-pure.py): a reader with no external tools at all
- [tools/cassini-pack.py](${site.repo}/blob/main/tools/cassini-pack.py): a complete producer, standard library only
- [tools/cassini-opus-digest.py](${site.repo}/blob/main/tools/cassini-opus-digest.py): the audio digest, written from its spec alone
- [tools/cassini-extract.py](${site.repo}/blob/main/tools/cassini-extract.py): decode a file with ffprobe
`;

	return new Response(body);
}
