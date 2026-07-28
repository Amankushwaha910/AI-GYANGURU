import { api } from './client';
import type { APIResponse, TokenResponse, User } from '$types';

export const authApi = {
	register: (data: { email: string; password: string; full_name?: string }) =>
		api.post<APIResponse<TokenResponse>>('/auth/register', data),

	login: (data: { email: string; password: string }) =>
		api.post<APIResponse<TokenResponse>>('/auth/login', data),

	logout: () => api.post<APIResponse<null>>('/auth/logout', {}),

	refresh: (refresh_token: string) =>
		api.post<APIResponse<TokenResponse>>('/auth/refresh', { refresh_token }),

	me: () => api.get<APIResponse<User>>('/auth/me'),

	changePassword: (data: { current_password: string; new_password: string }) =>
		api.put<APIResponse<null>>('/auth/password', data),

	googleLogin: (access_token: string) =>
		api.post<APIResponse<TokenResponse>>('/auth/google', { code: access_token })
};
