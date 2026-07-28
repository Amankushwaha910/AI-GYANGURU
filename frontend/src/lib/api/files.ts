import { apiFetch } from './client';
import { api } from './client';
import type { APIResponse, PaginatedResponse, Upload } from '$types';

export const filesApi = {
	upload: (file: File) => {
		const form = new FormData();
		form.append('file', file);
		return apiFetch<APIResponse<Upload>>('/files', { method: 'POST', body: form });
	},

	list: (params: { page?: number; page_size?: number } = {}) => {
		const q = new URLSearchParams();
		if (params.page) q.set('page', String(params.page));
		if (params.page_size) q.set('page_size', String(params.page_size));
		return api.get<PaginatedResponse<Upload>>(`/files?${q}`);
	},

	get: (id: string) => api.get<APIResponse<Upload>>(`/files/${id}`),

	delete: (id: string) => api.delete<APIResponse<null>>(`/files/${id}`)
};
