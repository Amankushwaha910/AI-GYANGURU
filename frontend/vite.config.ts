import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import os from 'os';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Redirect Vite's cache outside OneDrive to avoid file-locking issues
// that cause "UNKNOWN: unknown error, read" on Windows with OneDrive sync.
const cacheDir = path.join(os.tmpdir(), 'vite-gyanguru-cache');

export default defineConfig({
	plugins: [sveltekit()],
	cacheDir,
	// Explicitly set publicDir so Vite's viteServePublicMiddleware serves static/
	// Note: SvelteKit removes this middleware, but SvelteKit's own sirv also serves static/
	publicDir: path.join(__dirname, 'static'),
	server: {
		host: true,          // listen on 0.0.0.0 (IPv4 + IPv6)
		port: 5173,
		proxy: {
			'/api': {
				target: 'http://localhost:8000',
				changeOrigin: true
			}
		}
	}
});
