import { describe, expect, it } from 'vitest';
import { CASSINI_EMBED_SRC, CASSINI_EMBED_VERSION } from './embed';

describe('the Cassini embed this site loads', () => {
	it('is one exact published version, not a moving channel', () => {
		expect(CASSINI_EMBED_VERSION).not.toMatch(/^v\d+$/);
		expect(CASSINI_EMBED_SRC).toBe(
			`https://dist.gocassini.com/embed/${CASSINI_EMBED_VERSION}/viewer.js`
		);
	});
});
