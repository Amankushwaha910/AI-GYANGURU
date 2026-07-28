// ── API Response Wrappers ─────────────────────────────────────────────────────

export interface APIResponse<T> {
	success: boolean;
	data?: T;
	message?: string;
}

export interface PaginatedResponse<T> {
	success: boolean;
	data: T[];
	total: number;
	page: number;
	page_size: number;
	total_pages: number;
}

export interface APIError {
	success: false;
	error: {
		code: string;
		message: string;
	};
}

// ── Auth & User ───────────────────────────────────────────────────────────────

export type UserRole = 'student' | 'teacher' | 'admin';

export interface Profile {
	full_name: string | null;
	avatar_url: string | null;
	bio: string | null;
	education_level: string | null;
	exam_target: string | null;
	preferred_language: string;
}

export interface User {
	id: string;
	email: string;
	role: UserRole;
	is_active: boolean;
	is_email_verified: boolean;
	created_at: string;
	profile: Profile | null;
}

export interface TokenResponse {
	access_token: string;
	refresh_token: string;
	token_type: string;
}

// ── Summary ───────────────────────────────────────────────────────────────────

export type SummarySection =
	| 'definition'
	| 'key_concepts'
	| 'important_facts'
	| 'formula_sheet'
	| 'mnemonics'
	| 'exam_tips'
	| 'revision_notes'
	| 'checklist';

export interface Summary {
	id: string;
	topic: string;
	sections_requested: string[];
	content: Record<string, string>;
	model_used: string;
	is_from_file: boolean;
	word_count: number | null;
	created_at: string;
}

export interface SummaryListItem {
	id: string;
	topic: string;
	sections_requested: string[];
	is_from_file: boolean;
	created_at: string;
}

// ── Explanation ───────────────────────────────────────────────────────────────

export interface Explanation {
	id: string;
	topic: string;
	content: Record<string, string>;
	model_used: string;
	is_from_file: boolean;
	created_at: string;
}

export interface ExplanationListItem {
	id: string;
	topic: string;
	is_from_file: boolean;
	created_at: string;
}

// ── Quiz ──────────────────────────────────────────────────────────────────────

export type QuizDifficulty = 'easy' | 'medium' | 'hard' | 'mixed';

export interface QuizQuestion {
	id: string;
	order_index: number;
	question_text: string;
	options: string[];
	difficulty: string;
	category: string | null;
}

export interface Quiz {
	id: string;
	topic: string;
	difficulty: QuizDifficulty;
	category: string | null;
	question_count: number;
	model_used: string;
	is_from_file: boolean;
	questions: QuizQuestion[];
	created_at: string;
}

export interface QuizListItem {
	id: string;
	topic: string;
	difficulty: QuizDifficulty;
	question_count: number;
	is_from_file: boolean;
	created_at: string;
	latest_score: number | null;
}

export interface QuizResultQuestion {
	question_id: string;
	question_text: string;
	options: string[];
	selected_option: string | null;
	correct_option: string;
	is_correct: boolean;
	explanation: string;
}

export interface QuizAttempt {
	id: string;
	quiz_id: string;
	topic: string;
	score: number;
	total_questions: number;
	percentage: number;
	correct_count: number;
	wrong_count: number;
	time_taken_seconds: number | null;
	performance_summary: string | null;
	questions: QuizResultQuestion[];
	created_at: string;
}

// ── Upload ────────────────────────────────────────────────────────────────────

export type UploadStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface Upload {
	id: string;
	original_filename: string;
	file_type: string;
	file_size_bytes: number;
	status: UploadStatus;
	ocr_used: boolean;
	has_extracted_text: boolean;
	error_message: string | null;
	created_at: string;
}

// ── Analytics ─────────────────────────────────────────────────────────────────

export interface AnalyticsSummary {
	total_topics_studied: number;
	total_summaries_generated: number;
	total_explanations_generated: number;
	total_quizzes_taken: number;
	overall_quiz_accuracy: number;
}

export interface DailyActivityItem {
	date: string;
	count: number;
}

export interface CategoryAccuracy {
	category: string;
	accuracy: number;
	attempt_count: number;
}

export interface AnalyticsDashboard {
	summary: AnalyticsSummary;
	daily_activity: DailyActivityItem[];
	quiz_accuracy_trend: DailyActivityItem[];
	activity_heatmap: DailyActivityItem[];
	weak_areas: CategoryAccuracy[];
	strong_areas: CategoryAccuracy[];
}

// ── History ───────────────────────────────────────────────────────────────────

export type HistoryItemType = 'summary' | 'explanation' | 'quiz' | 'upload';

export interface HistoryItem {
	id: string;
	item_type: HistoryItemType;
	topic: string;
	resource_id: string;
	created_at: string;
}

// ── Dashboard ─────────────────────────────────────────────────────────────────

export interface RecentActivityItem {
	id: string;
	item_type: string;
	topic: string;
	resource_id: string;
	created_at: string;
}

export interface DashboardData {
	summary: AnalyticsSummary;
	recent_activity: RecentActivityItem[];
	weekly_activity: DailyActivityItem[];
	quiz_accuracy_week: DailyActivityItem[];
}
