/**
 * Base API client.
 * All API calls go through here — handles auth headers, errors, and token refresh.
 */
import { browser } from '$app/environment';
import { goto } from '$app/navigation';
import { authStore } from '$lib/stores/auth';
import type { APIError } from '$types';
import { get } from 'svelte/store';

const API_BASE = import.meta.env.PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';

export class ApiClientError extends Error {
	constructor(
		public code: string,
		message: string,
		public status: number
	) {
		super(message);
		this.name = 'ApiClientError';
	}
}

async function refreshAccessToken(): Promise<string | null> {
	const refresh_token = browser ? localStorage.getItem('refresh_token') : null;
	if (!refresh_token) return null;

	try {
		const res = await fetch(`${API_BASE}/auth/refresh`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ refresh_token })
		});
		if (!res.ok) return null;
		const data = await res.json();
		const newToken = data.data?.access_token;
		if (newToken && browser) {
			localStorage.setItem('access_token', newToken);
			if (data.data?.refresh_token) {
				localStorage.setItem('refresh_token', data.data.refresh_token);
			}
		}
		return newToken ?? null;
	} catch {
		return null;
	}
}

export async function apiFetch<T>(
	path: string,
	options: RequestInit = {},
	retry = true
): Promise<T> {
	const token = browser ? localStorage.getItem('access_token') : null;

	const headers: Record<string, string> = {
		'Content-Type': 'application/json',
		...(options.headers as Record<string, string>)
	};

	if (token) {
		headers['Authorization'] = `Bearer ${token}`;
	}

	// Remove Content-Type for FormData (browser sets it with boundary)
	if (options.body instanceof FormData) {
		delete headers['Content-Type'];
	}

	const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

	// Token expired — try refresh once
	if (res.status === 401 && retry) {
		const newToken = await refreshAccessToken();
		if (newToken) {
			return apiFetch<T>(path, options, false);
		} else {
			// Refresh failed — force logout
			authStore.clearAuth();
			if (browser) goto('/login');
			throw new ApiClientError('AUTH_ERROR', 'Session expired. Please log in again.', 401);
		}
	}

	const json = await res.json().catch(() => ({}));

	if (!res.ok) {
		const err = json as APIError;
		throw new ApiClientError(
			err.error?.code ?? 'UNKNOWN_ERROR',
			err.error?.message ?? `Request failed with status ${res.status}`,
			res.status
		);
	}

	return json as T;
}

/** Convenience wrappers */
export const api = {
	get: <T>(path: string) => apiFetch<T>(path, { method: 'GET' }),

	post: <T>(path: string, body: unknown) =>
		apiFetch<T>(path, {
			method: 'POST',
			body: JSON.stringify(body)
		}),

	put: <T>(path: string, body: unknown) =>
		apiFetch<T>(path, {
			method: 'PUT',
			body: JSON.stringify(body)
		}),

	delete: <T>(path: string) => apiFetch<T>(path, { method: 'DELETE' }),

	upload: <T>(path: string, formData: FormData) =>
		apiFetch<T>(path, {
			method: 'POST',
			body: formData
		})
};
