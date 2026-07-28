import { api } from './client';
import type { APIResponse, HistoryItem, HistoryItemType, PaginatedResponse } from '$types';

export const historyApi = {
	list: (params: {
		page?: number;
		page_size?: number;
		item_type?: HistoryItemType;
		search?: string;
	} = {}) => {
		const q = new URLSearchParams();
		if (params.page) q.set('page', String(params.page));
		if (params.page_size) q.set('page_size', String(params.page_size));
		if (params.item_type) q.set('item_type', params.item_type);
		if (params.search) q.set('search', params.search);
		return api.get<PaginatedResponse<HistoryItem>>(`/history?${q}`);
	},

	delete: (id: string) => api.delete<APIResponse<null>>(`/history/${id}`),

	clearByType: (item_type: HistoryItemType) =>
		api.delete<APIResponse<null>>(`/history?item_type=${item_type}`)
};
