/**
 * One place for the strings that appear on every page. The wire name is
 * CASSINI and stays CASSINI; keeping it here means the
 * whole site moves together if that ever changes.
 */
export const site = {
	name: 'Cassini',
	url: 'https://format.gocassini.com',
	formatName: 'Cassini portable meeting',
	tagPrefix: 'CASSINI_',
	formatId: 'org.cassini.portable-meeting/1',
	currentVersion: 1,
	repo: 'https://github.com/codemyriad/cassini-format',
	implRepo: 'https://github.com/codemyriad/gocassini',
	company: 'Code Myriad',
	companyUrl: 'https://codemyriad.io',
	description:
		'Audio and a timed transcript in one .opus file. Find a passage in the text, then listen to hear what was actually said. Made for our Nextcloud Talk app.'
};

export const versions = [
	{ id: 1, slug: 'v1', label: 'v1', status: 'current', wire: 'org.cassini.portable-meeting/1' }
] as const;

export const nav = [
	{ href: '/using/', label: 'Using Cassini' },
	{ href: '/try/', label: 'Open a file' },
	{ href: '/build/', label: 'Build with it' },
	{ href: '/spec/', label: 'Specification' }
];
