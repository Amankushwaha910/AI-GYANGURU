import { api } from './client';
import type { APIResponse, AnalyticsDashboard, DashboardData } from '$types';

export const analyticsApi = {
	getDashboard: () => api.get<APIResponse<AnalyticsDashboard>>('/analytics/dashboard'),
	getHomeDashboard: () => api.get<APIResponse<DashboardData>>('/dashboard')
};
