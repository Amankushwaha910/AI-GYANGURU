import { api } from './client';
import type {
	APIResponse,
	PaginatedResponse,
	Summary,
	SummaryListItem,
	SummarySection
} from '$types';

export const summariesApi = {
	generate: (data: { topic: string; sections: SummarySection[]; model?: string; provider?: string }) =>
		api.post<APIResponse<Summary>>('/summaries', data),

	generateFromFile: (data: { upload_id: string; sections: SummarySection[]; model?: string; provider?: string }) =>
		api.post<APIResponse<Summary>>('/summaries/from-file', data),

	list: (params: { page?: number; page_size?: number; search?: string } = {}) => {
		const q = new URLSearchParams();
		if (params.page) q.set('page', String(params.page));
		if (params.page_size) q.set('page_size', String(params.page_size));
		if (params.search) q.set('search', params.search);
		return api.get<PaginatedResponse<SummaryListItem>>(`/summaries?${q}`);
	},

	get: (id: string) => api.get<APIResponse<Summary>>(`/summaries/${id}`),

	delete: (id: string) => api.delete<APIResponse<null>>(`/summaries/${id}`)
};
