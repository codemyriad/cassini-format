import demo from '$lib/generated/demo.json';

export function load() {
	return { title: demo.readableTags.TITLE, filename: demo.generatedFrom };
}
