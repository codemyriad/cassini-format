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
		'An open file format for audio with embedded text: an ordinary .opus file that carries its own word-timestamped transcript, speaker labels and provenance in its OpusTags. For meeting recordings, podcasts and lyrics alike.'
};

export const versions = [
	{ id: 1, slug: 'v1', label: 'v1', status: 'current', wire: 'org.cassini.portable-meeting/1' }
] as const;

export const nav = [
	{ href: '/spec/v1/', label: 'Spec', key: 'S' },
	{ href: '/produce/', label: 'Produce', key: 'P' },
	{ href: '/consume/', label: 'Consume', key: 'C' },
	{ href: '/design/', label: 'Design notes', key: 'D' }
];
