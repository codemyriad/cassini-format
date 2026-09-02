import { site } from '$lib/site';
import { origin } from '$lib/origin';
import { listSchemas } from '$lib/docs';

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
It is this whole specification flattened into one document, with the places where
the prose has fallen behind the implementation marked inline. Reading SPEC.md
alone will produce a reader that rejects every file written today.

## Specification

- [The specification](${origin}/spec/v1/): what a producer writes and a consumer reads today
- [Transcript body, cassini.words.v1](${origin}/spec/words-v1/): one item per word, with a speaker and millisecond offsets
- [Audio digest, exact-opus-audio-v1](${origin}/spec/audio-integrity/): the byte rule that makes a recording's identity survive a tag rewrite
- [The whole document](${origin}/spec/document/): the specification on one page, rationale included

## Guides

- [Reading a file](${origin}/consume/): the eight steps, and every behaviour a reader has to decide
- [Writing a file](${origin}/produce/): numbered requirements, then conventions
- [Design notes](${origin}/design/): why it is shaped this way
- [Status](${origin}/status/): what is stable, what is still moving

## Schemas

${schemas.map((s) => `- [${s.title}](${origin}/schema/${s.file})`).join('\n')}

## A real file

- [lantern-festival.opus](${origin}/demo/lantern-festival.opus): a real ${site.formatId} file, 1.8 MB, six speakers, 669 word-timed items. Everything quoted on this site comes out of it.
- [How it was made](${origin}/demo/README.md)

## Reference code, all CC0

- [tools/cassini-read.js](${site.repo}/blob/main/tools/cassini-read.js): a browser reader, no dependencies
- [tools/cassini-read-pure.py](${site.repo}/blob/main/tools/cassini-read-pure.py): a reader with no external tools at all, ~110 lines
- [tools/cassini-pack.py](${site.repo}/blob/main/tools/cassini-pack.py): a complete producer, standard library only
- [tools/cassini-opus-digest.py](${site.repo}/blob/main/tools/cassini-opus-digest.py): the audio digest, written from its spec alone
- [tools/cassini-extract.py](${site.repo}/blob/main/tools/cassini-extract.py): decode a file with ffprobe
`;

	return new Response(body);
}
