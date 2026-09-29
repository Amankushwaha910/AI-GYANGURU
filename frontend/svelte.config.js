import adapter from '@sveltejs/adapter-auto';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';
import { fileURLToPath } from 'url';
import path from 'path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/** @type {import('@sveltejs/kit').Config} */
const config = {
	preprocess: vitePreprocess(),
	kit: {
		adapter: adapter(),
		// Use absolute path for static assets to avoid path resolution issues
		// on Windows with OneDrive (relative paths can break sirv middleware)
		files: {
			assets: path.join(__dirname, 'static')
		},
		alias: {
			$lib: './src/lib',
			$components: './src/lib/components',
			$stores: './src/lib/stores',
			$api: './src/lib/api',
			$types: './src/lib/types/index.ts'
		}
	}
};

export default config;
