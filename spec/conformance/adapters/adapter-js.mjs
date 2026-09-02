/* Conformance adapter for tools/cassini-read.js.
 * Takes one .opus path, prints one observation object, exits 0.
 * SPDX-License-Identifier: CC0-1.0 */
import { readFileSync } from 'node:fs';
import { readCassini } from '../../../tools/cassini-read.js';

const obs = { reader: 'tools/cassini-read.js', profile: 'metadata' };
const CODE = (m) =>
  /appears \d+ times/.test(m) ? 'duplicate-tag'
  : /is missing/.test(m) ? 'chunk-missing'
  : /CHUNK_COUNT is missing/.test(m) ? 'payload-descriptor-incomplete'
  : /not an Ogg|OpusTags/.test(m) ? 'not-opus'
  : 'decode-failed';

try {
  const b = readFileSync(process.argv[2]);
  const r = await readCassini(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength));
  if (!r.cassini) {
    Object.assign(obs, { state: 'plain-audio', classification: 'plain-audio',
                         payloadTrust: 'not-applicable',
                         audioTrust: 'not-applicable', errors: [], warnings: [] });
  } else {
    const bad = r.classification === 'damaged-metadata';
    Object.assign(obs, {
      // This reader never touches the audio, so a file it decodes cleanly is
      // 'unverified', not 'ok'. The spec says a consumer that never verifies
      // audio is conforming and must say so.
      state: bad ? 'invalid-cassini-metadata'
           : r.classification === 'unsupported-version' ? 'unknown-cassini-format'
           : 'unverified',
      classification: r.classification,
      // 'mismatched' means a digest was computed and disagreed. A chunk that
      // never arrived means no digest was ever computed, which is 'unverified'.
      payloadTrust: !bad
        ? (r.verified.manifest ? 'verified' : 'unverified')
        : (r.warnings.some((w) => w.code.endsWith('sha256-mismatch')) ? 'mismatched' : 'unverified'),
      audioTrust: 'not-checked',
      formatId: r.formatId,
      manifestVersion: r.manifest?.version ?? null,
      manifestKind: r.manifest?.kind ?? null,
      transcriptIds: (r.manifest?.transcripts ?? []).map((t) => t.id),
      defaultTranscriptId: r.transcript?.entry?.id ?? null,
      // this reader decodes only the default body, so it can only count that one
      wordCounts: r.transcript ? { [r.transcript.entry?.id ?? 'transcript']: r.transcript.words.length } : {},
      speakerIds: (r.manifest?.speakers ?? []).map((s) => s.id),
      // The reader names its own reasons; the adapter just passes them through.
      // An unavailable transcript is reported as an error too: the file is
      // fine, but the reader must say which body it could not load.
      errors: r.warnings.filter((w) => bad || r.unavailable).map((w) => ({ code: w.code, message: w.message })),
      warnings: r.warnings.filter((w) => !(bad || r.unavailable)).map((w) => ({ code: w.code, message: w.message })),
    });
  }
} catch (e) {
  const m = String(e.message ?? e);
  Object.assign(obs, { state: 'invalid-cassini-metadata',
                       classification: 'damaged-metadata', payloadTrust: 'unverified',
                       audioTrust: 'not-checked',
                       errors: [{ code: CODE(m), message: m }], warnings: [] });
}
console.log(JSON.stringify(obs));
