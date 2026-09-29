/**
 * SvelteKit server hooks.
 * Serves favicon and other root-level static assets that SvelteKit's
 * dev sirv middleware may not serve on Windows / OneDrive setups.
 */
import type { Handle } from '@sveltejs/kit';
import { readFileSync, existsSync } from 'fs';
import { join, extname } from 'path';

// process.cwd() in SvelteKit dev is always the project root (frontend/)
const staticDir = join(process.cwd(), 'static');

const MIME: Record<string, string> = {
	'.ico': 'image/x-icon',
	'.png': 'image/png',
	'.svg': 'image/svg+xml',
	'.jpg': 'image/jpeg',
	'.jpeg': 'image/jpeg',
	'.webp': 'image/webp',
	'.gif': 'image/gif',
};

export const handle: Handle = async ({ event, resolve }) => {
	const { pathname } = event.url;

	// Serve root-level static files (favicon.ico, favicon.png, etc.)
	// Only match paths with no subdirectory component (e.g. /favicon.ico, not /sub/file.png)
	if (pathname.match(/^\/[^/]+\.[a-z0-9]+$/i)) {
		const filePath = join(staticDir, pathname);
		if (existsSync(filePath)) {
			const ext = extname(filePath).toLowerCase();
			const mime = MIME[ext] ?? 'application/octet-stream';
			const body = readFileSync(filePath);
			return new Response(body, {
				headers: {
					'Content-Type': mime,
					'Cache-Control': 'public, max-age=3600'
				}
			});
		}
	}

	return resolve(event);
};
