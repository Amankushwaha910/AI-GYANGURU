import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
	return twMerge(clsx(inputs));
}

export function formatDate(dateStr: string): string {
	return new Date(dateStr).toLocaleDateString('en-IN', {
		year: 'numeric',
		month: 'short',
		day: 'numeric'
	});
}

export function formatRelativeTime(dateStr: string): string {
	const now = Date.now();
	const then = new Date(dateStr).getTime();
	const diff = Math.floor((now - then) / 1000);

	if (diff < 60) return 'just now';
	if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
	if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
	if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
	return formatDate(dateStr);
}

export function formatFileSize(bytes: number): string {
	if (bytes < 1024) return `${bytes} B`;
	if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
	return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function slugify(text: string): string {
	return text
		.toLowerCase()
		.replace(/\s+/g, '-')
		.replace(/[^\w-]/g, '')
		.slice(0, 60);
}

export const SECTION_LABELS: Record<string, string> = {
	definition: 'Definition',
	key_concepts: 'Key Concepts',
	important_facts: 'Important Facts',
	formula_sheet: 'Formula Sheet',
	mnemonics: 'Mnemonics',
	exam_tips: 'Exam Tips',
	revision_notes: 'Revision Notes',
	checklist: 'Checklist'
};

export const EXPLANATION_SECTION_LABELS: Record<string, string> = {
	introduction: 'Introduction',
	step_by_step: 'Step-by-Step Explanation',
	concept_breakdown: 'Concept Breakdown',
	real_examples: 'Real-World Examples',
	analogies: 'Analogies',
	practical_applications: 'Practical Applications',
	common_mistakes: 'Common Mistakes',
	faqs: 'FAQs',
	final_recap: 'Final Recap'
};

export const HISTORY_TYPE_LABELS: Record<string, string> = {
	summary: 'Summary',
	explanation: 'Explanation',
	quiz: 'Quiz',
	upload: 'Upload'
};

export const HISTORY_TYPE_COLORS: Record<string, string> = {
	summary: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
	explanation: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
	quiz: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
	upload: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300'
};
