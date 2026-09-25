import adapter from '@sveltejs/adapter-static';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

// Set BASE_PATH=/cassini-format for a project-subpath deploy (GitHub Pages).
// Leave it unset for a root-domain deploy, which is what we build for.
const base = (process.env.BASE_PATH ?? '') as '' | `/${string}`;

export default defineConfig({
	plugins: [
		sveltekit({
			compilerOptions: {
				runes: ({ filename }: { filename: string }) =>
					filename.split(/[/\\]/).some((part) => part === 'node_modules' || part === 'vendor')
						? undefined
						: true
			},
			adapter: adapter({
				pages: 'build',
				assets: 'build',
				fallback: '404.html',
				precompress: false,
				strict: true
			}),
			paths: { base, relative: false },
			prerender: {
				// These two turn the build into a link and anchor checker for the spec.
				handleHttpError: 'fail',
				handleMissingId: 'fail',
				// '*' covers every route reachable by crawling. /karaoke/ is unlisted
				// (noindex, no link from the nav or the footer), so it is named here or
				// the static build would not emit it.
				entries: ['*', '/karaoke/']
			},
			alias: { $repo: '../' }
		})
	]
});
