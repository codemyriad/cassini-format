/**
 * One place for the strings that appear on every page. The wire name is
 * CASSINI and stays CASSINI; keeping it here means the
 * whole site moves together if that ever changes.
 */
export const site = {
	name: 'Cassini',
	formatName: 'Cassini portable meeting',
	tagPrefix: 'CASSINI_',
	formatId: 'org.cassini.portable-meeting/1',
	currentVersion: 1,
	repo: 'https://github.com/codemyriad/cassini-format',
	implRepo: 'https://github.com/codemyriad/gocassini',
	company: 'Code Myriad',
	companyUrl: 'https://codemyriad.io',
	description:
		'Audio, a word-timed transcript and speaker labels in one ordinary .opus file. Explore the open Cassini format, try a file in your browser, or build a reader of your own.'
};

export const versions = [
	{ id: 1, slug: 'v1', label: 'v1', status: 'current', wire: 'org.cassini.portable-meeting/1' }
] as const;

export const nav = [
	{ href: '/try/', label: 'Try it' },
	{ href: '/consume/', label: 'Read a file' },
	{ href: '/produce/', label: 'Write a file' },
	{ href: '/spec/', label: 'Specification' }
];
