/**
 * Auth store — manages current user, tokens, and session state.
 */
import { browser } from '$app/environment';
import { writable, derived, get } from 'svelte/store';
import type { User } from '$types';

interface AuthState {
	user: User | null;
	accessToken: string | null;
	refreshToken: string | null;
	loading: boolean;
	initialized: boolean;
}

function createAuthStore() {
	const { subscribe, set, update } = writable<AuthState>({
		user: null,
		accessToken: null,
		refreshToken: null,
		loading: true,
		initialized: false
	});

	return {
		subscribe,

		setTokens(accessToken: string, refreshToken: string) {
			if (browser) {
				localStorage.setItem('access_token', accessToken);
				localStorage.setItem('refresh_token', refreshToken);
			}
			update((s) => ({ ...s, accessToken, refreshToken }));
		},

		setUser(user: User) {
			update((s) => ({ ...s, user, loading: false, initialized: true }));
		},

		clearAuth() {
			if (browser) {
				localStorage.removeItem('access_token');
				localStorage.removeItem('refresh_token');
			}
			set({ user: null, accessToken: null, refreshToken: null, loading: false, initialized: true });
		},

		setLoading(loading: boolean) {
			update((s) => ({ ...s, loading }));
		},

		init() {
			if (!browser) return;
			const accessToken = localStorage.getItem('access_token');
			const refreshToken = localStorage.getItem('refresh_token');
			update((s) => ({ ...s, accessToken, refreshToken, initialized: true }));
		}
	};
}

export const authStore = createAuthStore();

// Derived helpers
export const isAuthenticated = derived(authStore, ($auth) => !!$auth.user);
export const currentUser = derived(authStore, ($auth) => $auth.user);
export const isAuthLoading = derived(authStore, ($auth) => $auth.loading);
