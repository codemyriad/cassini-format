/**
 * A Cassini portable meeting reader for the browser. No dependencies.
 *
 * It walks the Ogg pages, finds the OpusTags comment header, reassembles the
 * chunked payload, inflates it with the platform's own gzip, verifies both
 * SHA-256 digests, and hands back the manifest and the words.
 *
 * Everything it needs is in the file. That is the whole claim the format makes,
 * so this file is also the proof of it.
 *
 * SPDX-License-Identifier: CC0-1.0
 */
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
function* packets(buf, limit = 2) {
    const view = new DataView(buf);
    const bytes = new Uint8Array(buf);
    let offset = 0;
    let pending = [];
    let yielded = 0;
    while (offset + 27 <= bytes.length) {
        if (view.getUint32(offset, true) !== MAGIC_OGG) {
            throw new Error(`not an Ogg stream: no OggS capture pattern at byte ${offset}`);
        }
        const segments = bytes[offset + 26];
        const tableAt = offset + 27;
        const dataAt = tableAt + segments;
        if (dataAt > bytes.length)
            break;
        // A continued page whose packet we are not tracking means we joined mid-stream.
        if (!(bytes[offset + 5] & CONTINUED))
            pending = [];
        let cursor = dataAt;
        let run = 0;
        for (let i = 0; i < segments; i++) {
            const size = bytes[tableAt + i];
            run += size;
            if (size === 255)
                continue;
            pending.push(bytes.subarray(cursor, cursor + run));
            cursor += run;
            run = 0;
            yield concat(pending);
            pending = [];
            if (++yielded >= limit)
                return;
        }
        if (run > 0) {
            pending.push(bytes.subarray(cursor, cursor + run));
            cursor += run;
        }
        offset = cursor;
    }
    if (pending.length)
        yield concat(pending);
}
function concat(parts) {
    if (parts.length === 1)
        return parts[0];
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
 */
export function parseOpusTags(packet) {
    const text = new TextDecoder('utf-8', { fatal: false });
    if (text.decode(packet.subarray(0, 8)) !== 'OpusTags') {
        throw new Error('second packet is not OpusTags');
    }
    const view = new DataView(packet.buffer, packet.byteOffset, packet.byteLength);
    let at = 8;
    const vendorLen = view.getUint32(at, true);
    at += 4 + vendorLen;
    const count = view.getUint32(at, true);
    at += 4;
    const tags = new Map();
    for (let i = 0; i < count && at + 4 <= packet.length; i++) {
        const len = view.getUint32(at, true);
        at += 4;
        if (at + len > packet.length)
            break;
        const raw = text.decode(packet.subarray(at, at + len));
        at += len;
        const eq = raw.indexOf('=');
        if (eq < 1)
            continue;
        const key = raw.slice(0, eq).toUpperCase();
        const list = tags.get(key);
        if (list)
            list.push(raw.slice(eq + 1));
        else
            tags.set(key, [raw.slice(eq + 1)]);
    }
    return tags;
}
const one = (tags, key) => tags.get(key)?.[0];
/* -------------------------------------------------------------------------- */
/* Payload                                                                     */
/* -------------------------------------------------------------------------- */
/** The producer writes unpadded base64url. Put the padding back before decoding. */
function base64urlToBytes(text) {
    const padded = text.replace(/-/g, '+').replace(/_/g, '/') + '='.repeat((4 - (text.length % 4)) % 4);
    const binary = atob(padded);
    const out = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++)
        out[i] = binary.charCodeAt(i);
    return out;
}
async function gunzip(data) {
    const stream = new Blob([data]).stream().pipeThrough(new DecompressionStream('gzip'));
    try {
        return new Uint8Array(await new Response(stream).arrayBuffer());
    }
    catch (cause) {
        // A corrupted payload surfaces here as a bare TypeError from the stream
        // adapter, which tells the caller nothing.
        throw new Error('gzip decompress failed: the payload is corrupt', { cause });
    }
}
async function sha256Hex(data) {
    const digest = await crypto.subtle.digest('SHA-256', data);
    return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, '0')).join('');
}
/** An error that already knows which conformance code describes it. */
class ChunkError extends Error {
    code;
    constructor(code, message) {
        super(message);
        this.code = code;
    }
}
const issue = (e, fallback) => ({
    code: e instanceof ChunkError ? e.code : fallback,
    message: e instanceof Error ? e.message : String(e)
});
/**
 * Reassemble a chunk set by tag index, inflate it, and parse it.
 * Chunks are joined in numeric order, never in the order the tags happen to appear.
 */
async function decodeChunkSet(tags, prefix, chunkCount, expectSha) {
    let blob = '';
    for (let i = 0; i < chunkCount; i++) {
        const key = `${prefix}${String(i).padStart(3, '0')}`;
        const values = tags.get(key);
        if (!values)
            throw new ChunkError('chunk-missing', `chunk ${key} is missing`);
        if (values.length > 1) {
            throw new ChunkError('duplicate-tag', `chunk ${key} appears ${values.length} times`);
        }
        blob += values[0];
    }
    const raw = await gunzip(base64urlToBytes(blob));
    const verified = expectSha ? (await sha256Hex(raw)) === expectSha.toLowerCase() : null;
    return { value: JSON.parse(new TextDecoder().decode(raw)), verified };
}
/* -------------------------------------------------------------------------- */
/* The reader                                                                  */
/* -------------------------------------------------------------------------- */
export async function readCassini(buf) {
    const warnings = [];
    const [, tagsPacket] = [...packets(buf, 2)];
    if (!tagsPacket)
        throw new Error('no OpusTags packet: this is not an Ogg Opus file');
    const tags = parseOpusTags(tagsPacket);
    const formatId = one(tags, 'CASSINI_FORMAT');
    if (!formatId) {
        // Rule 1: no Cassini metadata means this is plain audio, and that is fine.
        return {
            classification: 'plain-audio',
            cassini: false,
            tags,
            verified: { manifest: null, transcript: null },
            warnings
        };
    }
    const version = Number(/\/(\d+)$/.exec(formatId)?.[1] ?? NaN);
    const chunkCount = Number(one(tags, 'CASSINI_PAYLOAD_CHUNK_COUNT') ?? NaN);
    if (!Number.isFinite(chunkCount))
        throw new Error('CASSINI_PAYLOAD_CHUNK_COUNT is missing');
    // A malformed payload is damaged metadata over valid audio, not a broken
    // file. Report it and let the caller fall back to playing the recording.
    let main;
    try {
        main = await decodeChunkSet(tags, 'CASSINI_PAYLOAD_', chunkCount, one(tags, 'CASSINI_PAYLOAD_SHA256'));
    }
    catch (e) {
        warnings.push(issue(e, 'payload-decode-failed'));
        return {
            classification: 'damaged-metadata',
            cassini: true,
            formatId,
            version,
            tags,
            verified: { manifest: false, transcript: null },
            warnings
        };
    }
    const manifest = main.value;
    if (main.verified === false) {
        warnings.push({
            code: 'payload-sha256-mismatch',
            message: 'the manifest does not match CASSINI_PAYLOAD_SHA256'
        });
    }
    // The private drafts inlined a single transcript. The published format
    // indexes them and puts each body in its own chunk set.
    if (manifest.transcript?.items) {
        return {
            classification: main.verified === false ? 'damaged-metadata' : 'cassini',
            cassini: true,
            formatId,
            version,
            tags,
            manifest,
            transcript: { words: manifest.transcript.items },
            verified: { manifest: main.verified, transcript: null },
            warnings
        };
    }
    // The manifest is the record and the tag is a copy of it, so the manifest's
    // own default flag resolves first. The tag is a fallback for when the
    // manifest says nothing, and a disagreement between them is worth reporting
    // but is never an error.
    const list = manifest.transcripts ?? [];
    const wanted = one(tags, 'CASSINI_TRANSCRIPT_DEFAULT');
    const entry = list.find((t) => t.default) ??
        list.find((t) => t.id === wanted) ??
        list.find((t) => t.role === 'raw-asr') ??
        list[0];
    if (wanted && entry && entry.id !== wanted) {
        warnings.push({
            code: 'tag-manifest-disagreement',
            message: `CASSINI_TRANSCRIPT_DEFAULT names "${wanted}"; the manifest flags "${entry.id}". Using the manifest.`
        });
    }
    if (!entry) {
        warnings.push({ code: 'no-transcripts', message: 'the manifest indexes no transcripts' });
        return {
            classification: main.verified === false ? 'damaged-metadata' : 'cassini',
            cassini: true,
            formatId,
            version,
            tags,
            manifest,
            verified: { manifest: main.verified, transcript: null },
            warnings
        };
    }
    let body;
    try {
        body = await decodeChunkSet(tags, entry.payloadRef.prefix.toUpperCase(), entry.payloadRef.chunkCount, entry.payloadRef.sha256);
    }
    catch (e) {
        // The manifest survived, so the meeting metadata is still worth showing.
        warnings.push(issue(e, 'transcript-decode-failed'));
        return {
            classification: 'damaged-metadata',
            cassini: true,
            formatId,
            version,
            tags,
            manifest,
            verified: { manifest: main.verified, transcript: false },
            warnings
        };
    }
    if (body.verified === false) {
        warnings.push({
            code: 'transcript-sha256-mismatch',
            message: `transcript "${entry.id}" does not match its payloadRef.sha256`
        });
    }
    return {
        classification: main.verified === false || body.verified === false ? 'damaged-metadata' : 'cassini',
        cassini: true,
        formatId,
        version,
        tags,
        manifest,
        transcript: { entry, words: body.value.items ?? [] },
        verified: { manifest: main.verified, transcript: body.verified },
        warnings
    };
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
export function toTurns(words, speakers) {
    const labels = new Map(speakers.map((s) => [s.id, s.label ?? s.id]));
    const turns = [];
    for (const word of words) {
        const last = turns.at(-1);
        if (last && last.speaker === word.speaker) {
            last.words.push(word);
            last.endMs = Math.max(last.endMs, word.endMs);
        }
        else {
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
