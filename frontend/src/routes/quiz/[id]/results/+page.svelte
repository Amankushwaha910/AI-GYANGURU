<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { quizzesApi } from '$lib/api/quizzes';
	import { toast } from '$lib/stores/toast';
	import type { QuizAttempt } from '$lib/types';
	import Button from '$lib/components/ui/Button.svelte';
	import Card from '$lib/components/ui/Card.svelte';
	import PageLayout from '$lib/components/layout/PageLayout.svelte';
	import { CheckCircle, XCircle, ChevronDown, ChevronUp, RefreshCw, BarChart2 } from 'lucide-svelte';

	const quizId = $page.params.id!;
	const attemptId = $page.url.searchParams.get('attempt') ?? '';

	let attempt: QuizAttempt | null = null;
	let loading = true;
	let expandedId: string | null = null;

	onMount(async () => {
		try {
			const res = await quizzesApi.getAttempt(quizId, attemptId);
			attempt = res.data ?? null;
		} catch {
			toast.error('Failed to load results');
		} finally {
			loading = false;
		}
	});

	$: grade = (() => {
		const p = attempt?.percentage ?? 0;
		if (p >= 90) return { label: 'Excellent!', color: 'text-green-600 dark:text-green-400', ring: 'stroke-green-500', bg: 'from-green-50 to-white dark:from-green-950/30 dark:to-gray-900', emoji: '🏆' };
		if (p >= 75) return { label: 'Great Job!', color: 'text-blue-600 dark:text-blue-400', ring: 'stroke-blue-500', bg: 'from-blue-50 to-white dark:from-blue-950/30 dark:to-gray-900', emoji: '🎯' };
		if (p >= 50) return { label: 'Good Effort', color: 'text-yellow-600 dark:text-yellow-400', ring: 'stroke-yellow-500', bg: 'from-yellow-50 to-white dark:from-yellow-950/30 dark:to-gray-900', emoji: '💪' };
		return { label: 'Keep Practicing', color: 'text-red-600 dark:text-red-400', ring: 'stroke-red-500', bg: 'from-red-50 to-white dark:from-red-950/30 dark:to-gray-900', emoji: '📚' };
	})();
</script>

<svelte:head><title>Results — AI GyanGuru</title></svelte:head>

<PageLayout title="Quiz Results">
	{#if loading}
		<div class="flex justify-center py-20">
			<div class="h-10 w-10 animate-spin rounded-full border-4 border-green-200 border-t-green-600"></div>
		</div>
	{:else if attempt}
		<!-- Score card -->
		<Card padding="lg" class="mb-6 bg-gradient-to-br {grade.bg}">
			<div class="flex flex-col items-center text-center py-4">
				<span class="text-5xl mb-3">{grade.emoji}</span>
				<h2 class="text-2xl font-bold {grade.color}">{grade.label}</h2>

				<!-- Circular progress -->
				<div class="relative my-5">
					<svg class="h-28 w-28 -rotate-90" viewBox="0 0 100 100">
						<circle cx="50" cy="50" r="42" fill="none" stroke-width="8" class="stroke-gray-200 dark:stroke-gray-700" />
						<circle
							cx="50" cy="50" r="42" fill="none" stroke-width="8"
							stroke-dasharray="{2 * Math.PI * 42}"
							stroke-dashoffset="{2 * Math.PI * 42 * (1 - (attempt.percentage / 100))}"
							stroke-linecap="round"
							class="{grade.ring} transition-all duration-1000"
						/>
					</svg>
					<div class="absolute inset-0 flex flex-col items-center justify-center">
						<span class="text-2xl font-bold text-gray-900 dark:text-white">{attempt.percentage.toFixed(0)}%</span>
					</div>
				</div>

				<div class="flex gap-6">
					<div class="text-center">
						<p class="text-2xl font-bold text-green-600 dark:text-green-400">{attempt.correct_count}</p>
						<p class="text-xs text-gray-500 dark:text-gray-400">Correct</p>
					</div>
					<div class="w-px bg-gray-200 dark:bg-gray-700"></div>
					<div class="text-center">
						<p class="text-2xl font-bold text-red-600 dark:text-red-400">{attempt.wrong_count}</p>
						<p class="text-xs text-gray-500 dark:text-gray-400">Wrong</p>
					</div>
					<div class="w-px bg-gray-200 dark:bg-gray-700"></div>
					<div class="text-center">
						<p class="text-2xl font-bold text-gray-700 dark:text-gray-300">{attempt.total_questions}</p>
						<p class="text-xs text-gray-500 dark:text-gray-400">Total</p>
					</div>
				</div>
			</div>
		</Card>

		<!-- AI Feedback -->
		{#if attempt.performance_summary}
			<Card padding="md" class="mb-6 border-l-4 border-brand-500">
				<p class="text-xs font-semibold text-brand-600 dark:text-brand-400 uppercase tracking-wider mb-2">AI Feedback</p>
				<p class="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{attempt.performance_summary}</p>
			</Card>
		{/if}

		<!-- Question-by-question review -->
		<div class="mb-8">
			<h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4">
				Question Review
			</h3>
			<div class="space-y-3">
				{#each attempt.questions as q, i}
					<div class="rounded-xl border-2 overflow-hidden transition-all {q.is_correct ? 'border-green-200 dark:border-green-900' : 'border-red-200 dark:border-red-900'}">
						<!-- Question header -->
						<button
							class="w-full flex items-center gap-3 p-4 text-left bg-white dark:bg-gray-900 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
							on:click={() => expandedId = expandedId === q.question_id ? null : q.question_id}
						>
							{#if q.is_correct}
								<CheckCircle class="h-5 w-5 text-green-500 flex-shrink-0" />
							{:else}
								<XCircle class="h-5 w-5 text-red-500 flex-shrink-0" />
							{/if}
							<span class="flex-1 text-sm font-medium text-gray-800 dark:text-gray-200 text-left leading-snug">
								{i + 1}. {q.question_text}
							</span>
							{#if expandedId === q.question_id}
								<ChevronUp class="h-4 w-4 text-gray-400 flex-shrink-0" />
							{:else}
								<ChevronDown class="h-4 w-4 text-gray-400 flex-shrink-0" />
							{/if}
						</button>

						<!-- Expanded review -->
						{#if expandedId === q.question_id}
							<div class="border-t border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-800/40 p-4 space-y-4">
								<!-- Options -->
								<div class="space-y-2">
									{#each q.options as opt, idx}
										{@const letter = ['A','B','C','D'][idx]}
										{@const isCorrect = letter === q.correct_option}
										{@const isWrong = letter === q.selected_option && !q.is_correct}
										<div class="flex items-start gap-2.5 rounded-lg px-3 py-2 text-sm transition-colors
										{isCorrect ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300' :
										 isWrong   ? 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300' :
										             'text-gray-600 dark:text-gray-400'}">
											<span class="font-bold flex-shrink-0 w-4">{letter}.</span>
											<span class="flex-1">{opt.replace(/^[A-D]\.\s*/, '')}</span>
											{#if isCorrect}
												<CheckCircle class="h-4 w-4 flex-shrink-0" />
											{:else if isWrong}
												<XCircle class="h-4 w-4 flex-shrink-0" />
											{/if}
										</div>
									{/each}
								</div>

								<!-- Your answer vs correct -->
								{#if !q.is_correct}
									<div class="flex flex-wrap gap-4 text-xs">
										<span class="text-red-600 dark:text-red-400">
											Your answer: <strong>{q.selected_option ?? 'Not answered'}</strong>
										</span>
										<span class="text-green-600 dark:text-green-400">
											Correct: <strong>{q.correct_option}</strong>
										</span>
									</div>
								{/if}

								<!-- Explanation -->
								<div class="rounded-xl bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800 p-3">
									<p class="text-xs font-semibold text-blue-600 dark:text-blue-400 mb-1.5">Explanation</p>
									<p class="text-xs text-blue-700 dark:text-blue-300 leading-relaxed">{q.explanation}</p>
								</div>
							</div>
						{/if}
					</div>
				{/each}
			</div>
		</div>

		<!-- Actions -->
		<div class="flex flex-wrap gap-3">
			<Button href="/quiz" variant="primary">
				<RefreshCw class="h-4 w-4" /> New Quiz
			</Button>
			<Button href="/analytics" variant="secondary">
				<BarChart2 class="h-4 w-4" /> View Analytics
			</Button>
			<Button href="/history" variant="ghost">View History</Button>
		</div>
	{/if}
</PageLayout>
