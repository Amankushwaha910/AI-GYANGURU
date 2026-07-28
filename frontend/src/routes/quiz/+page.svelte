<script lang="ts">
	import { goto } from '$app/navigation';
	import { quizzesApi } from '$api/quizzes';
	import { toast } from '$stores/toast';
	import { ApiClientError } from '$api/client';
	import type { QuizDifficulty } from '$types';
	import Button from '$components/ui/Button.svelte';
	import Input from '$components/ui/Input.svelte';
	import Card from '$components/ui/Card.svelte';
	import Select from '$components/ui/Select.svelte';
	import PageLayout from '$components/layout/PageLayout.svelte';
	import { HelpCircle, Sparkles } from 'lucide-svelte';

	let topic = '';
	let questionCount = '10';
	let difficulty: QuizDifficulty = 'mixed';
	let category = '';
	let loading = false;
	let error = '';

	const difficultyOptions = [
		{ value: 'easy', label: 'Easy' },
		{ value: 'medium', label: 'Medium' },
		{ value: 'hard', label: 'Hard' },
		{ value: 'mixed', label: 'Mixed' }
	];

	const countOptions = [
		{ value: '5', label: '5 Questions' },
		{ value: '10', label: '10 Questions' },
		{ value: '15', label: '15 Questions' },
		{ value: '20', label: '20 Questions' }
	];

	async function generate() {
		if (!topic.trim()) { error = 'Please enter a topic'; return; }
		error = ''; loading = true;
		try {
			const res = await quizzesApi.generate({
				topic: topic.trim(),
				question_count: parseInt(questionCount),
				difficulty,
				category: category.trim() || undefined
			});
			if (res.data) {
				toast.success('Quiz ready! Starting now...');
				goto(`/quiz/${res.data.id}/play`);
			}
		} catch (e: any) {
			error = e instanceof ApiClientError ? e.message : 'Failed to generate quiz.';
			toast.error(error);
		} finally { loading = false; }
	}
</script>

<svelte:head><title>Quiz — AI GyanGuru</title></svelte:head>

<PageLayout title="AI Quiz" subtitle="Test your knowledge with AI-generated MCQs">
	<div class="max-w-xl mx-auto">
		<Card padding="lg">
			<div class="flex items-center gap-3 mb-6">
				<div class="h-10 w-10 rounded-xl bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
					<HelpCircle class="h-5 w-5 text-green-600 dark:text-green-400" />
				</div>
				<div>
					<h2 class="font-bold text-gray-900 dark:text-white">Generate a Quiz</h2>
					<p class="text-sm text-gray-500 dark:text-gray-400">AI creates unique MCQs every time</p>
				</div>
			</div>

			<form on:submit|preventDefault={generate} class="space-y-5">
				{#if error}
					<div class="rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 px-4 py-3 text-sm text-red-700 dark:text-red-300">{error}</div>
				{/if}

				<Input label="Topic" placeholder="e.g. French Revolution" bind:value={topic} required />

				<div class="grid grid-cols-2 gap-4">
					<Select label="Questions" bind:value={questionCount} options={countOptions} />
					<Select label="Difficulty" bind:value={difficulty} options={difficultyOptions} />
				</div>

				<Input label="Category (Optional)" placeholder="e.g. History, Science, Math" bind:value={category} />

				<Button type="submit" {loading} disabled={loading} class="w-full" size="lg">
					<Sparkles class="h-4 w-4" />
					{loading ? 'Generating Quiz...' : 'Generate Quiz'}
				</Button>
			</form>
		</Card>

		<div class="mt-4 rounded-xl bg-green-50 dark:bg-green-900/20 border border-green-100 dark:border-green-800 p-4">
			<p class="text-sm font-medium text-green-700 dark:text-green-300 mb-1">How it works</p>
			<ul class="text-xs text-green-600 dark:text-green-400 space-y-1">
				<li>• AI generates unique MCQs based on your topic</li>
				<li>• Each question has 4 options with one correct answer</li>
				<li>• After submission, you'll see explanations for every question</li>
				<li>• Your score and weak areas are tracked automatically</li>
			</ul>
		</div>
	</div>
</PageLayout>
