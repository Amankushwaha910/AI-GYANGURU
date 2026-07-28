<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { quizzesApi } from '$lib/api/quizzes';
	import { toast } from '$lib/stores/toast';
	import type { Quiz } from '$lib/types';
	import type { SubmitAnswerItem } from '$lib/api/quizzes';
	import Button from '$lib/components/ui/Button.svelte';
	import Card from '$lib/components/ui/Card.svelte';

	const quizId = $page.params.id!;

	let quiz: Quiz | null = null;
	let loading = true;
	let submitting = false;
	let currentIndex = 0;
	let answers: Record<string, string | null> = {};
	let startTime = Date.now();

	onMount(async () => {
		try {
			const res = await quizzesApi.get(quizId);
			quiz = res.data ?? null;
			startTime = Date.now();
		} catch {
			toast.error('Failed to load quiz');
			goto('/quiz');
		} finally {
			loading = false;
		}
	});

	$: currentQuestion = quiz?.questions[currentIndex];
	$: totalQuestions = quiz?.questions.length ?? 0;
	$: progress = totalQuestions > 0 ? ((currentIndex + 1) / totalQuestions) * 100 : 0;
	$: answeredCount = Object.values(answers).filter(Boolean).length;
	$: canSubmit = answeredCount >= 1;

	const optionLetters = ['A', 'B', 'C', 'D'];

	function selectOption(questionId: string, option: string) {
		answers = { ...answers, [questionId]: option };
	}

	function prev() { if (currentIndex > 0) currentIndex--; }
	function next() { if (quiz && currentIndex < quiz.questions.length - 1) currentIndex++; }

	async function submitQuiz() {
		if (!quiz || !canSubmit) return;
		submitting = true;
		const elapsed = Math.floor((Date.now() - startTime) / 1000);
		const submitAnswers: SubmitAnswerItem[] = quiz.questions.map(q => ({
			question_id: q.id,
			selected_option: answers[q.id] ?? null
		}));
		try {
			const res = await quizzesApi.submit(quizId, {
				answers: submitAnswers,
				time_taken_seconds: elapsed
			});
			if (res.data) {
				toast.success('Quiz submitted!');
				goto(`/quiz/${quizId}/results?attempt=${res.data.id}`);
			}
		} catch {
			toast.error('Submission failed. Please try again.');
		} finally {
			submitting = false;
		}
	}
</script>

<svelte:head><title>Quiz — AI GyanGuru</title></svelte:head>

<div class="flex flex-col min-h-screen bg-gray-50 dark:bg-gray-950">
	{#if loading}
		<div class="flex flex-1 items-center justify-center">
			<div class="h-10 w-10 animate-spin rounded-full border-4 border-green-200 border-t-green-600"></div>
		</div>
	{:else if quiz && currentQuestion}
		<!-- Progress bar -->
		<div class="w-full h-1.5 bg-gray-200 dark:bg-gray-800 fixed top-0 left-0 z-10">
			<div class="h-full bg-green-500 transition-all duration-500" style="width: {progress}%"></div>
		</div>

		<div class="flex-1 max-w-3xl mx-auto w-full px-6 pt-10 pb-8">
			<!-- Header -->
			<div class="flex items-center justify-between mb-6">
				<div>
					<p class="text-sm text-gray-500 dark:text-gray-400">
						Question <span class="font-bold text-gray-800 dark:text-gray-200">{currentIndex + 1}</span> of {totalQuestions}
					</p>
					<h1 class="font-bold text-gray-900 dark:text-white text-lg truncate max-w-sm">{quiz.topic}</h1>
				</div>
				<div class="text-right hidden sm:block">
					<p class="text-sm text-gray-500">{answeredCount} / {totalQuestions} answered</p>
					<span class="text-xs capitalize font-medium text-gray-400">{quiz.difficulty}</span>
				</div>
			</div>

			<!-- Question nav dots -->
			<div class="flex flex-wrap gap-1.5 mb-6">
				{#each quiz.questions as q, i}
					<button
						on:click={() => currentIndex = i}
						class="h-7 w-7 rounded-lg text-xs font-bold transition-all {
							i === currentIndex
								? 'bg-green-600 text-white shadow-sm'
								: answers[q.id]
								? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
								: 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400 hover:bg-gray-200'
						}"
					>{i + 1}</button>
				{/each}
			</div>

			<!-- Question -->
			<Card padding="lg" class="mb-5">
				<div class="flex items-start gap-3">
					<span class="flex-shrink-0 h-7 w-7 rounded-lg bg-green-100 dark:bg-green-900/30 flex items-center justify-center text-sm font-bold text-green-700 dark:text-green-300">
						{currentIndex + 1}
					</span>
					<p class="text-base font-semibold text-gray-900 dark:text-white leading-relaxed">
						{currentQuestion.question_text}
					</p>
				</div>
				{#if currentQuestion.category}
					<p class="mt-3 text-xs text-gray-400 pl-10">Category: {currentQuestion.category}</p>
				{/if}
			</Card>

			<!-- Options -->
			<div class="space-y-3 mb-8">
				{#each currentQuestion.options as option, i}
					{@const letter = optionLetters[i]}
					{@const selected = answers[currentQuestion.id] === letter}
					<button
						on:click={() => selectOption(currentQuestion.id, letter)}
						class="group w-full flex items-start gap-4 rounded-xl border-2 p-4 text-left transition-all duration-150
						{selected
							? 'border-green-500 bg-green-50 dark:bg-green-900/20 dark:border-green-500'
							: 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 hover:border-green-300 dark:hover:border-green-800 hover:bg-green-50/50 dark:hover:bg-green-900/10'
						}"
					>
						<span class="flex-shrink-0 h-7 w-7 rounded-lg flex items-center justify-center text-sm font-bold transition-colors
						{selected ? 'bg-green-600 text-white' : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 group-hover:bg-green-100 dark:group-hover:bg-green-900/30'}">
							{letter}
						</span>
						<span class="text-sm text-gray-800 dark:text-gray-200 leading-relaxed pt-0.5">
							{option.replace(/^[A-D]\.\s*/, '')}
						</span>
					</button>
				{/each}
			</div>

			<!-- Navigation -->
			<div class="flex items-center justify-between">
				<Button variant="secondary" on:click={prev} disabled={currentIndex === 0}>
					← Previous
				</Button>

				<div class="flex items-center gap-3">
					{#if canSubmit}
						<Button
							variant="outline"
							size="sm"
							on:click={submitQuiz}
							disabled={submitting}
							loading={submitting}
						>
							Submit ({answeredCount}/{totalQuestions})
						</Button>
					{/if}

					{#if currentIndex < totalQuestions - 1}
						<Button variant="primary" on:click={next}>
							Next →
						</Button>
					{:else}
						<Button
							variant="primary"
							on:click={submitQuiz}
							disabled={!canSubmit || submitting}
							loading={submitting}
						>
							Submit Quiz
						</Button>
					{/if}
				</div>
			</div>
		</div>
	{/if}
</div>
