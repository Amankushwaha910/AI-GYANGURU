import { api } from './client';
import type { APIResponse, Explanation, ExplanationListItem, PaginatedResponse } from '$types';

export const explanationsApi = {
	generate: (data: { topic: string; model?: string; provider?: string }) =>
		api.post<APIResponse<Explanation>>('/explanations', data),

	generateFromFile: (data: { upload_id: string; model?: string; provider?: string }) =>
		api.post<APIResponse<Explanation>>('/explanations/from-file', data),

	list: (params: { page?: number; page_size?: number; search?: string } = {}) => {
		const q = new URLSearchParams();
		if (params.page) q.set('page', String(params.page));
		if (params.page_size) q.set('page_size', String(params.page_size));
		if (params.search) q.set('search', params.search);
		return api.get<PaginatedResponse<ExplanationListItem>>(`/explanations?${q}`);
	},

	get: (id: string) => api.get<APIResponse<Explanation>>(`/explanations/${id}`),

	delete: (id: string) => api.delete<APIResponse<null>>(`/explanations/${id}`)
};
