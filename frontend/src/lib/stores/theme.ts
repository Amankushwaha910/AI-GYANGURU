/**
 * Theme store — dark/light mode with system preference detection and persistence.
 */
import { browser } from '$app/environment';
import { writable } from 'svelte/store';

type Theme = 'light' | 'dark';

function createThemeStore() {
	const getInitial = (): Theme => {
		if (!browser) return 'light';
		const stored = localStorage.getItem('theme') as Theme | null;
		if (stored) return stored;
		return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
	};

	const { subscribe, set, update } = writable<Theme>(getInitial());

	const apply = (theme: Theme) => {
		if (!browser) return;
		document.documentElement.classList.toggle('dark', theme === 'dark');
		localStorage.setItem('theme', theme);
	};

	return {
		subscribe,
		toggle() {
			update((t) => {
				const next: Theme = t === 'dark' ? 'light' : 'dark';
				apply(next);
				return next;
			});
		},
		set(theme: Theme) {
			apply(theme);
			set(theme);
		},
		init() {
			const t = getInitial();
			apply(t);
			set(t);
		}
	};
}

export const themeStore = createThemeStore();
