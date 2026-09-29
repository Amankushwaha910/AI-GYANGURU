import { api } from './client';
import type { APIResponse, AIModelsResponse } from '$types';

export const modelsApi = {
	list: () => api.get<APIResponse<AIModelsResponse>>('/models')
};
