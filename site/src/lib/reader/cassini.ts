/**
 * A Cassini portable meeting reader for the browser. No dependencies.
 *
 * It walks the Ogg pages, finds the OpusTags comment header, reassembles the
 * chunked payload, inflates it with the platform's own gzip, verifies the
 * manifest and transcript digests, and hands back the manifest and the words.
 *
 * It never reads the audio, so the best state it can report is `unverified`.
 * That is what the specification says a metadata-only reader must say.
 *
 * Everything it needs is in the file. That is the whole claim the format makes,
 * so this file is also the proof of it.
 *
 * SPDX-License-Identifier: CC0-1.0
 */

export type Word = {
	speaker: string;
	startMs: number;
	endMs: number;
	text: string;
	/** Present only on words the attribution stage measured. */
	attributionGapDb?: number;
	/** Only ever true. A confidently attributed word omits the key. */
	lowConfidenceSpeaker?: boolean;
};

export type Speaker = { id: string; label?: string };

export type PayloadRef = {
	prefix: string;
	chunkCount: number;
	sha256: string;
	rawBytes?: number;
	gzipBytes?: number;
	mime?: string;
	encoding?: string;
};

export type TranscriptEntry = {
	id: string;
	role: string;
	default?: boolean;
	format: string;
	language?: string;
	wordCount?: number;
	sourceTranscriptId?: string;
	payloadRef: PayloadRef;
};

export type Manifest = {
	kind: string;
	version: number;
	profile: string;
	meeting: Record<string, unknown> & { title?: string; durationMs?: number; id?: string };
	audio: Record<string, unknown>;
	integrity: Record<string, unknown>;
	speakers: Speaker[];
	transcripts?: TranscriptEntry[];
	readableTranscripts?: TranscriptEntry[];
	provenance?: Record<string, unknown>;
	[key: string]: unknown;
};

/**
 * A machine-readable reason, so a caller can branch without matching prose.
 * The message is for a human; the code is the contract.
 */
export type Issue = { code: IssueCode; message: string };

export type IssueCode =
	| 'unsupported-version'
	| 'payload-descriptor-incomplete'
	| 'chunk-missing'
	| 'duplicate-tag'
	| 'payload-decode-failed'
	| 'payload-sha256-mismatch'
	| 'manifest-invalid'
	| 'transcript-decode-failed'
	| 'transcript-sha256-mismatch'
	| 'no-transcripts'
	| 'tag-manifest-disagreement';

/**
 * The six normative trust states. This reader never checks the audio, so it
 * never reports `stale-audio` or `ok`.
 */
export type State =
	| 'plain-audio'
	| 'unknown-cassini-format'
	| 'invalid-cassini-metadata'
	| 'unverified'
	| 'stale-audio'
	| 'ok';

/**
 * A coarser label for callers that branch on what to show.
 *
 *   plain-audio          no Cassini metadata; play it, this is not an error
 *   cassini              the manifest decoded and verified
 *   damaged-metadata     Cassini metadata present, the manifest is unusable
 *   unsupported-version  a major version this reader does not implement
 */
export type Classification = 'plain-audio' | 'cassini' | 'damaged-metadata' | 'unsupported-version';

export type ReadResult = {
	state: State;
	classification: Classification;
	/** false when the file is ordinary audio with no Cassini metadata. */
	cassini: boolean;
	formatId?: string;
	version?: number;
	tags: Map<string, string[]>;
	/** Absent unless it decoded and matched its digest. Never a partial manifest. */
	manifest?: Manifest;
	/** Absent when the file has none or the chosen one could not be loaded. */
	transcript?: { entry: TranscriptEntry; words: Word[] };
	/** The transcript entry that was chosen but could not be loaded, if any. */
	unavailable?: { entry: TranscriptEntry; reason: Issue };
	verified: { manifest: boolean | null; transcript: boolean | null };
	warnings: Issue[];
};

const FORMAT_PREFIX = 'org.cassini.portable-meeting/';
const KNOWN_MAJOR = 1;
const KIND = 'cassini-portable-meeting';
/** No declared length can raise this. A meeting transcript is kilobytes. */
const INFLATE_CEILING = 64 * 1024 * 1024;

const MAGIC_OGG = 0x5367674f; // "OggS", little-endian
const CONTINUED = 0x01;

/* -------------------------------------------------------------------------- */
/* Ogg                                                                         */
/* -------------------------------------------------------------------------- */

/**
 * Yield the first `limit` packets of the logical bitstream.
 *
 * A packet is a run of lacing segments ending in one shorter than 255, and it
 * can straddle pages. A 60 KB comment header spans several pages, so getting
 * this right is not an edge case, it is the normal path.
 */
function* packets(buf: ArrayBuffer, limit = 2): Generator<Uint8Array> {
	const view = new DataView(buf);
	const bytes = new Uint8Array(buf);
	let offset = 0;
	let pending: Uint8Array[] = [];
	let yielded = 0;

	while (offset + 27 <= bytes.length) {
		if (view.getUint32(offset, true) !== MAGIC_OGG) {
			throw new Error(`not an Ogg stream: no OggS capture pattern at byte ${offset}`);
		}
		const segments = bytes[offset + 26];
		const tableAt = offset + 27;
		const dataAt = tableAt + segments;
		if (dataAt > bytes.length) break;

		// A continued page whose packet we are not tracking means we joined mid-stream.
		if (!(bytes[offset + 5] & CONTINUED)) pending = [];

		let cursor = dataAt;
		let run = 0;
		for (let i = 0; i < segments; i++) {
			const size = bytes[tableAt + i];
			run += size;
			if (size === 255) continue;
			pending.push(bytes.subarray(cursor, cursor + run));
			cursor += run;
			run = 0;
			yield concat(pending);
			pending = [];
			if (++yielded >= limit) return;
		}
		if (run > 0) {
			pending.push(bytes.subarray(cursor, cursor + run));
			cursor += run;
		}
		offset = cursor;
	}
	if (pending.length) yield concat(pending);
}

function concat(parts: Uint8Array[]): Uint8Array {
	if (parts.length === 1) return parts[0];
	const total = parts.reduce((n, p) => n + p.length, 0);
	const out = new Uint8Array(total);
	let at = 0;
	for (const p of parts) {
		out.set(p, at);
		at += p.length;
	}
	return out;
}

/* -------------------------------------------------------------------------- */
/* OpusTags                                                                    */
/* -------------------------------------------------------------------------- */

/**
 * Parse the Vorbis comment vector out of an OpusTags packet.
 *
 * Field names are case-insensitive per the Vorbis comment spec, so they are
 * upper-cased on the way in. They are also not unique: the same name may appear
 * more than once, which is why this returns a multimap.
 *
 * A truncated vector or a comment that is not UTF-8 is a malformed header, and
 * this throws rather than return half of it.
 */
export function parseOpusTags(packet: Uint8Array): Map<string, string[]> {
	const text = new TextDecoder('utf-8', { fatal: true });
	const ascii = (b: Uint8Array) => String.fromCharCode(...b);
	if (packet.length < 16 || ascii(packet.subarray(0, 8)) !== 'OpusTags') {
		throw new Error('second packet is not OpusTags');
	}
	const view = new DataView(packet.buffer, packet.byteOffset, packet.byteLength);
	let at = 8;
	const vendorLen = view.getUint32(at, true);
	at += 4 + vendorLen;
	if (at + 4 > packet.length) throw new Error('OpusTags is truncated');
	const count = view.getUint32(at, true);
	at += 4;

	const tags = new Map<string, string[]>();
	for (let i = 0; i < count; i++) {
		if (at + 4 > packet.length) throw new Error('OpusTags is truncated');
		const len = view.getUint32(at, true);
		at += 4;
		if (at + len > packet.length) throw new Error('OpusTags is truncated');
		let raw: string;
		try {
			raw = text.decode(packet.subarray(at, at + len));
		} catch {
			throw new Error(`OpusTags comment ${i} is not valid UTF-8`);
		}
		at += len;
		const eq = raw.indexOf('=');
		if (eq < 1) continue;
		const key = raw.slice(0, eq).toUpperCase();
		const list = tags.get(key);
		if (list) list.push(raw.slice(eq + 1));
		else tags.set(key, [raw.slice(eq + 1)]);
	}
	return tags;
}

const one = (tags: Map<string, string[]>, key: string) => tags.get(key)?.[0];

/** A decimal integer as the specification spells it: no sign, no leading zero, safe. */
function decimal(text: string | undefined): number | undefined {
	if (text === undefined || !/^(0|[1-9][0-9]*)$/.test(text.trim())) return undefined;
	const n = Number(text.trim());
	return Number.isSafeInteger(n) ? n : undefined;
}

/* -------------------------------------------------------------------------- */
/* Payload                                                                     */
/* -------------------------------------------------------------------------- */

/** The producer writes unpadded base64url. Put the padding back before decoding. */
function base64urlToBytes(text: string): Uint8Array {
	const padded = text.replace(/-/g, '+').replace(/_/g, '/') + '='.repeat((4 - (text.length % 4)) % 4);
	const binary = atob(padded);
	const out = new Uint8Array(binary.length);
	for (let i = 0; i < binary.length; i++) out[i] = binary.charCodeAt(i);
	return out;
}

/**
 * Inflate, and stop the moment the output passes `limit`. The declared length
 * is untrusted: it bounds the read, it never raises the ceiling.
 */
async function gunzip(data: Uint8Array, limit: number): Promise<Uint8Array> {
	const stream = new Blob([data as BlobPart]).stream().pipeThrough(new DecompressionStream('gzip'));
	const reader = stream.getReader();
	const parts: Uint8Array[] = [];
	let total = 0;
	try {
		for (;;) {
			const { done, value } = await reader.read();
			if (done) break;
			total += value.length;
			if (total > limit) {
				await reader.cancel();
				throw new ChunkError(
					'payload-decode-failed',
					`the payload inflates past its declared ${limit} bytes`
				);
			}
			parts.push(value);
		}
	} catch (cause) {
		if (cause instanceof ChunkError) throw cause;
		// A corrupted payload surfaces here as a bare TypeError from the stream
		// adapter, which tells the caller nothing.
		throw new Error('gzip decompress failed: the payload is corrupt', { cause });
	}
	return concat(parts);
}

async function sha256Hex(data: Uint8Array): Promise<string> {
	const digest = await crypto.subtle.digest('SHA-256', data as BufferSource);
	return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, '0')).join('');
}

/** An error that already knows which conformance code describes it. */
class ChunkError extends Error {
	constructor(
		readonly code: IssueCode,
		message: string
	) {
		super(message);
	}
}

const issue = (e: unknown, fallback: IssueCode): Issue => ({
	code: e instanceof ChunkError ? e.code : fallback,
	message: e instanceof Error ? e.message : String(e)
});

/**
 * Reassemble a chunk set by tag index, inflate it, and parse it.
 * Chunks are joined in numeric order, never in the order the tags happen to appear.
 */
async function decodeChunkSet(
	tags: Map<string, string[]>,
	prefix: string,
	chunkCount: number,
	expectSha: string | undefined,
	rawBytes: number | undefined
): Promise<{ value: unknown; verified: boolean | null }> {
	let blob = '';
	for (let i = 0; i < chunkCount; i++) {
		const key = `${prefix}${String(i).padStart(3, '0')}`;
		const values = tags.get(key);
		if (!values) throw new ChunkError('chunk-missing', `chunk ${key} is missing`);
		if (values.length > 1) {
			throw new ChunkError('duplicate-tag', `chunk ${key} appears ${values.length} times`);
		}
		blob += values[0];
	}
	const limit = Math.min(rawBytes ?? INFLATE_CEILING, INFLATE_CEILING);
	const raw = await gunzip(base64urlToBytes(blob), limit);
	const verified = expectSha ? (await sha256Hex(raw)) === expectSha.toLowerCase() : null;
	return { value: JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(raw)), verified };
}

/** Any load-bearing name that appears twice makes the file invalid. */
function repeatedLoadBearing(tags: Map<string, string[]>): string | undefined {
	for (const [key, values] of tags) {
		if (values.length < 2) continue;
		if (key === 'CASSINI_FORMAT' || key.startsWith('CASSINI_PAYLOAD_') || key.startsWith('CASSINI_TX_'))
			return key;
	}
	return undefined;
}

const WORD_ROLES = new Set(['raw-asr', 'human-corrected', 'translation', 'scripted']);

/* -------------------------------------------------------------------------- */
/* The reader                                                                  */
/* -------------------------------------------------------------------------- */

export async function readCassini(buf: ArrayBuffer): Promise<ReadResult> {
	const warnings: Issue[] = [];
	const [, tagsPacket] = [...packets(buf, 2)];
	if (!tagsPacket) throw new Error('no OpusTags packet: this is not an Ogg Opus file');
	const tags = parseOpusTags(tagsPacket);

	const formatId = one(tags, 'CASSINI_FORMAT');
	if (!formatId) {
		// No Cassini metadata means this is plain audio, and that is fine.
		return {
			state: 'plain-audio',
			classification: 'plain-audio',
			cassini: false,
			tags,
			verified: { manifest: null, transcript: null },
			warnings
		};
	}

	const invalid = (w: Issue, version?: number): ReadResult => {
		warnings.push(w);
		return {
			state: 'invalid-cassini-metadata',
			classification: 'damaged-metadata',
			cassini: true,
			formatId,
			version,
			tags,
			verified: { manifest: false, transcript: null },
			warnings
		};
	};

	// A major version this reader does not implement: play the audio, say so,
	// and touch nothing else. The chunk transport is not promised across majors.
	const major = formatId.startsWith(FORMAT_PREFIX)
		? decimal(formatId.slice(FORMAT_PREFIX.length))
		: undefined;
	if (major !== KNOWN_MAJOR) {
		warnings.push({
			code: 'unsupported-version',
			message: `${formatId} is not a version this reader implements`
		});
		return {
			state: 'unknown-cassini-format',
			classification: 'unsupported-version',
			cassini: true,
			formatId,
			version: major,
			tags,
			verified: { manifest: null, transcript: null },
			warnings
		};
	}

	const repeated = repeatedLoadBearing(tags);
	if (repeated) {
		return invalid(
			{ code: 'duplicate-tag', message: `${repeated} appears ${tags.get(repeated)!.length} times` },
			major
		);
	}

	const chunkCount = decimal(one(tags, 'CASSINI_PAYLOAD_CHUNK_COUNT'));
	if (chunkCount === undefined || chunkCount < 1) {
		return invalid(
			{
				code: 'payload-descriptor-incomplete',
				message: 'CASSINI_PAYLOAD_CHUNK_COUNT is missing or not a positive decimal integer'
			},
			major
		);
	}
	const sha = one(tags, 'CASSINI_PAYLOAD_SHA256');
	if (!sha) {
		return invalid(
			{ code: 'payload-descriptor-incomplete', message: 'CASSINI_PAYLOAD_SHA256 is missing' },
			major
		);
	}

	// A malformed payload is damaged metadata over valid audio, not a broken
	// file. Report it and let the caller fall back to playing the recording.
	let main: { value: unknown; verified: boolean | null };
	try {
		main = await decodeChunkSet(
			tags,
			'CASSINI_PAYLOAD_',
			chunkCount,
			sha,
			decimal(one(tags, 'CASSINI_PAYLOAD_RAW_BYTES'))
		);
	} catch (e) {
		return invalid(issue(e, 'payload-decode-failed'), major);
	}
	if (main.verified === false) {
		// Check before believing any field. A manifest that fails its digest is
		// not shown, not even partially.
		return invalid(
			{ code: 'payload-sha256-mismatch', message: 'the manifest does not match CASSINI_PAYLOAD_SHA256' },
			major
		);
	}

	const manifest = main.value as Manifest;
	if (!manifest || typeof manifest !== 'object' || manifest.kind !== KIND) {
		return invalid({ code: 'manifest-invalid', message: `manifest.kind is not ${KIND}` }, major);
	}
	if (manifest.version !== major) {
		return invalid(
			{
				code: 'manifest-invalid',
				message: `manifest.version ${manifest.version} disagrees with ${formatId}`
			},
			major
		);
	}

	const good = (extra: Partial<ReadResult>): ReadResult => ({
		state: 'unverified',
		classification: 'cassini',
		cassini: true,
		formatId,
		version: major,
		tags,
		manifest,
		verified: { manifest: true, transcript: null },
		warnings,
		...extra
	});

	// The manifest is the record and the tag is a copy of it. The words slot is
	// the first entry flagged default, failing that the first entry; the tag is
	// only ever compared, never used to choose.
	const list = (manifest.transcripts ?? []).filter((t) => WORD_ROLES.has(t.role));
	const entry = list.find((t) => t.default) ?? list[0];
	const wanted = one(tags, 'CASSINI_TRANSCRIPT_DEFAULT');
	if (wanted && entry && entry.id !== wanted) {
		warnings.push({
			code: 'tag-manifest-disagreement',
			message: `CASSINI_TRANSCRIPT_DEFAULT names "${wanted}"; the manifest resolves "${entry.id}". Using the manifest.`
		});
	}
	if (!entry) {
		warnings.push({ code: 'no-transcripts', message: 'the manifest indexes no word-timed transcript' });
		return good({});
	}

	// A body that will not load makes that transcript unavailable, not the file.
	// The meeting, the speakers and the other transcripts are still good.
	const ref = entry.payloadRef;
	let body: { value: unknown; verified: boolean | null };
	try {
		body = await decodeChunkSet(
			tags,
			ref.prefix.toUpperCase(),
			ref.chunkCount,
			ref.sha256,
			typeof ref.rawBytes === 'number' ? ref.rawBytes : undefined
		);
	} catch (e) {
		const reason = issue(e, 'transcript-decode-failed');
		warnings.push({ ...reason, message: `transcript "${entry.id}" is unavailable: ${reason.message}` });
		return good({ unavailable: { entry, reason }, verified: { manifest: true, transcript: false } });
	}
	if (body.verified === false) {
		const reason: Issue = {
			code: 'transcript-sha256-mismatch',
			message: `transcript "${entry.id}" does not match its payloadRef.sha256`
		};
		warnings.push({ ...reason, message: `transcript "${entry.id}" is unavailable: ${reason.message}` });
		return good({ unavailable: { entry, reason }, verified: { manifest: true, transcript: false } });
	}

	const items = (body.value as { items?: Word[] | null })?.items ?? [];
	return good({
		transcript: { entry, words: items },
		verified: { manifest: true, transcript: body.verified }
	});
}

/**
 * Group words into speaker turns.
 *
 * A turn is a maximal run of consecutive items with the same speaker, and that
 * is the whole rule: no time-gap heuristic. Items arrive in speaker-turn order,
 * not sorted by time, because overlapping speech keeps each speaker's words
 * together. Anything that reorders or re-splits them by timestamp destroys the
 * turns.
 */
export function toTurns(words: Word[], speakers: Speaker[]) {
	const labels = new Map(speakers.map((s) => [s.id, s.label ?? s.id]));
	const turns: { speaker: string; label: string; startMs: number; endMs: number; words: Word[] }[] =
		[];
	for (const word of words) {
		const last = turns.at(-1);
		if (last && last.speaker === word.speaker) {
			last.words.push(word);
			last.endMs = Math.max(last.endMs, word.endMs);
		} else {
			turns.push({
				speaker: word.speaker,
				label: labels.get(word.speaker) ?? word.speaker,
				startMs: word.startMs,
				endMs: word.endMs,
				words: [word]
			});
		}
	}
	return turns;
}
