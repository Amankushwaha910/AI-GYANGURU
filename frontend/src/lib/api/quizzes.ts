import { api } from './client';
import type {
	APIResponse,
	PaginatedResponse,
	Quiz,
	QuizAttempt,
	QuizDifficulty,
	QuizListItem
} from '$types';

export interface SubmitAnswerItem {
	question_id: string;
	selected_option: string | null;
}

export const quizzesApi = {
	generate: (data: {
		topic: string;
		question_count?: number;
		difficulty?: QuizDifficulty;
		category?: string;
		model?: string;
	}) => api.post<APIResponse<Quiz>>('/quizzes', data),

	generateFromFile: (data: {
		upload_id: string;
		question_count?: number;
		difficulty?: QuizDifficulty;
		category?: string;
		model?: string;
	}) => api.post<APIResponse<Quiz>>('/quizzes/from-file', data),

	list: (params: { page?: number; page_size?: number; search?: string } = {}) => {
		const q = new URLSearchParams();
		if (params.page) q.set('page', String(params.page));
		if (params.page_size) q.set('page_size', String(params.page_size));
		if (params.search) q.set('search', params.search);
		return api.get<PaginatedResponse<QuizListItem>>(`/quizzes?${q}`);
	},

	get: (id: string) => api.get<APIResponse<Quiz>>(`/quizzes/${id}`),

	submit: (
		quizId: string,
		data: { answers: SubmitAnswerItem[]; time_taken_seconds?: number }
	) => api.post<APIResponse<QuizAttempt>>(`/quizzes/${quizId}/submit`, data),

	getAttempt: (quizId: string, attemptId: string) =>
		api.get<APIResponse<QuizAttempt>>(`/quizzes/${quizId}/attempts/${attemptId}`)
};
