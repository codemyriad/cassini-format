import { describe, expect, it } from 'vitest';
import { readFile } from 'node:fs/promises';
import { meetingStart, readCassini } from './cassini';

const vector = async (name: string) => {
	const b = await readFile(new URL(`../../../../spec/conformance/opus/${name}.opus`, import.meta.url));
	return readCassini(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength));
};

// Every vector here also carries a recordedAtLocal of UTC digits and a
// createdAtUtc an hour after the meeting. Neither may win.
describe('meetingStart', () => {
	it('takes recordedAtUtc over the label and the pack stamp', async () => {
		const read = await vector('027-recorded-at-utc');
		expect(read.tags.get('CASSINI_RECORDED_AT_UTC')).toEqual(['2026-11-09T09:31:48.250Z']);
		expect(read.tags.get('DATE')).toEqual(['2026-11-09T09:31:48.250Z']);
		expect(meetingStart(read)).toEqual({
			source: 'recordedAtUtc',
			value: '2026-11-09T09:31:48.250Z',
			instantMs: Date.UTC(2026, 10, 9, 9, 31, 48, 250)
		});
	});

	it('ignores a DATE that is only the pack stamp, and never converts the label', async () => {
		const read = await vector('028-date-is-created-at');
		expect(meetingStart(read)).toEqual({
			source: 'recordedAtLocal',
			value: '2026-11-09T09:31:48',
			instantMs: null
		});
	});

	it('takes a DATE with an offset when it is not the pack stamp', async () => {
		const read = await vector('029-date-with-offset');
		expect(meetingStart(read)).toEqual({
			source: 'DATE',
			value: '2026-11-09T10:31:48+01:00',
			instantMs: Date.UTC(2026, 10, 9, 9, 31, 48)
		});
	});

	it('has no answer for a file that names no meeting time', async () => {
		const read = await vector('001-minimal-v1');
		expect(read.manifest?.meeting.createdAtUtc).toBeTruthy();
		expect(meetingStart(read)).toBeNull();
	});
});
