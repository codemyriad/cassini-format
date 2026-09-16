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
	/** The app that implements this format: recorder, transcriber and packer. */
	appUrl: 'https://gocassini.com',
	appName: 'gocassini',
	company: 'Code Myriad',
	companyUrl: 'https://codemyriad.io',
	description:
		'An ordinary Ogg .opus file that carries its own transcript, speakers and provenance in its tags. Open specification, version 1, with CC0 schemas and readers.'
};

export const versions = [
	{ id: 1, slug: 'v1', label: 'v1', status: 'current', wire: 'org.cassini.portable-meeting/1' }
] as const;

/**
 * Three things a specification site has to communicate: the spec, the tools for
 * working with files, and who implements it. Implementations live on the home
 * page rather than a route of their own.
 */
export const nav = [
	{ href: '/spec/', label: 'Spec' },
	{ href: '/build/', label: 'Tools' },
	{ href: '/#implementations', label: 'Implementations' }
];
