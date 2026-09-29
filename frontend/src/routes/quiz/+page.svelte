<script lang="ts">
	import { goto } from '$app/navigation';
	import { quizzesApi } from '$api/quizzes';
	import { filesApi } from '$api/files';
	import { toast } from '$stores/toast';
	import { ApiClientError } from '$api/client';
	import { modelSelector } from '$stores/modelSelector';
	import { onMount } from 'svelte';
	import type { QuizDifficulty, Upload } from '$types';
	import { formatFileSize } from '$lib/utils';
	import Button from '$components/ui/Button.svelte';
	import Input from '$components/ui/Input.svelte';
	import Card from '$components/ui/Card.svelte';
	import Select from '$components/ui/Select.svelte';
	import PageLayout from '$components/layout/PageLayout.svelte';
	import ModelSelector from '$components/ui/ModelSelector.svelte';
	import { HelpCircle, Sparkles, ChevronDown } from 'lucide-svelte';
	import { page } from '$app/stores';

	// ── State ──────────────────────────────────────────────────────────────────
	let topic = '';
	let questionCount = '10';
	let difficulty: QuizDifficulty = 'mixed';
	let category = '';
	let loading = false;
	let error = '';

	let sourceMode: 'topic' | 'file' = 'topic';
	let readyUploads: Upload[] = [];
	let selectedUploadId = '';
	let loadingUploads = false;

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

	onMount(async () => {
		const urlUploadId = $page.url.searchParams.get('upload_id');
		loadingUploads = true;
		try {
			const res = await filesApi.list({ page: 1, page_size: 50 });
			readyUploads = res.data.filter(u => u.status === 'completed');
			if (urlUploadId && readyUploads.some(u => u.id === urlUploadId)) {
				sourceMode = 'file';
				selectedUploadId = urlUploadId;
			}
		} catch { /* non-critical */ } finally {
			loadingUploads = false;
		}
	});

	async function generate() {
		if (sourceMode === 'topic' && !topic.trim()) { error = 'Please enter a topic'; return; }
		if (sourceMode === 'file' && !selectedUploadId) { error = 'Please select an uploaded file'; return; }
		error = '';
		loading = true;

		const { provider, model } = modelSelector.getSelection();

		try {
			let res;
			if (sourceMode === 'file') {
				res = await quizzesApi.generateFromFile({
					upload_id: selectedUploadId,
					question_count: parseInt(questionCount),
					difficulty,
					category: category.trim() || undefined,
					model,
					provider,
				});
			} else {
				res = await quizzesApi.generate({
					topic: topic.trim(),
					question_count: parseInt(questionCount),
					difficulty,
					category: category.trim() || undefined,
					model,
					provider,
				});
			}

			if (res.data) {
				toast.success('Quiz ready! Starting now…');
				goto(`/quiz/${res.data.id}/play`);
			}
		} catch (e: any) {
			error = e instanceof ApiClientError ? e.message : 'Failed to generate quiz.';
			toast.error(error);
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head><title>Quiz — AI GyanGuru</title></svelte:head>

<PageLayout title="AI Quiz" subtitle="Test your knowledge with AI-generated MCQs from any topic or document">

	<!-- ── Input card (full width) ──────────────────────────────────────────── -->
	<Card padding="lg" class="mb-6">
		<div class="flex items-center gap-3 mb-6">
			<div class="h-9 w-9 rounded-xl bg-green-100 dark:bg-green-900/30 flex items-center justify-center flex-shrink-0">
				<HelpCircle class="h-5 w-5 text-green-600 dark:text-green-400" />
			</div>
			<div>
				<h2 class="font-bold text-gray-900 dark:text-white">Generate a Quiz</h2>
				<p class="text-sm text-gray-500 dark:text-gray-400">AI creates unique MCQs every time</p>
			</div>
		</div>

		<form on:submit|preventDefault={generate} class="space-y-5">

			<!-- Source mode tabs -->
			<div class="flex gap-1 rounded-xl bg-gray-100 dark:bg-gray-800 p-1 w-fit">
				<button type="button" on:click={() => { sourceMode = 'topic'; error = ''; }}
					class="rounded-lg px-4 py-1.5 text-sm font-medium transition-all
					       {sourceMode === 'topic' ? 'bg-white dark:bg-gray-900 text-gray-900 dark:text-white shadow-sm' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700'}">
					Topic
				</button>
				<button type="button" on:click={() => { sourceMode = 'file'; error = ''; }}
					class="rounded-lg px-4 py-1.5 text-sm font-medium transition-all
					       {sourceMode === 'file' ? 'bg-white dark:bg-gray-900 text-gray-900 dark:text-white shadow-sm' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700'}">
					Uploaded File
				</button>
			</div>

			{#if error}
				<div class="rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 px-4 py-3 text-sm text-red-700 dark:text-red-300">
					{error}
				</div>
			{/if}

			{#if sourceMode === 'topic'}
				<Input label="Topic" placeholder="e.g. French Revolution" bind:value={topic} required />
			{:else}
				<div>
					<label for="file-select-quiz" class="text-sm font-medium text-gray-700 dark:text-gray-300 block mb-1.5">Select Uploaded File</label>
					{#if loadingUploads}
						<p class="text-sm text-gray-400">Loading your files…</p>
					{:else if readyUploads.length === 0}
						<p class="text-sm text-gray-500 dark:text-gray-400">
							No processed files yet.
							<a href="/upload" class="text-brand-600 dark:text-brand-400 hover:underline font-medium">Upload a file</a> first.
						</p>
					{:else}
						<div class="relative">
							<select id="file-select-quiz" bind:value={selectedUploadId}
								class="w-full h-10 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 px-4 pr-9 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-500 appearance-none">
								<option value="">— Choose a file —</option>
								{#each readyUploads as u}
									<option value={u.id}>{u.original_filename} ({formatFileSize(u.file_size_bytes)})</option>
								{/each}
							</select>
							<ChevronDown class="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
						</div>
					{/if}
				</div>
			{/if}

			<!-- Question count + difficulty on one row -->
			<div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
				<Select label="Questions" bind:value={questionCount} options={countOptions} />
				<Select label="Difficulty" bind:value={difficulty} options={difficultyOptions} />
				<div class="sm:col-span-2">
					<Input label="Category (Optional)" placeholder="e.g. History, Science, Math" bind:value={category} />
				</div>
			</div>

			<!-- AI Model -->
			<div>
				<p class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">AI Model</p>
				<ModelSelector />
			</div>

			<Button type="submit" {loading} disabled={loading} size="lg">
				<Sparkles class="h-4 w-4" />
				{loading ? 'Generating Quiz…' : 'Generate Quiz'}
			</Button>
		</form>
	</Card>

	<!-- ── How it works info box ─────────────────────────────────────────────── -->
	{#if !loading}
		<div class="rounded-xl bg-green-50 dark:bg-green-900/20 border border-green-100 dark:border-green-800 p-4">
			<p class="text-sm font-medium text-green-700 dark:text-green-300 mb-1">How it works</p>
			<ul class="text-xs text-green-600 dark:text-green-400 space-y-1">
				<li>• AI generates unique MCQs based on your topic or uploaded document content</li>
				<li>• Each question has 4 options with one correct answer</li>
				<li>• After submission, you'll see explanations for every question</li>
				<li>• Your score and weak areas are tracked automatically</li>
			</ul>
		</div>
	{/if}

	<!-- Quiz navigates away on success, so no result panel needed here -->
	{#if loading}
		<Card padding="lg" class="mt-6">
			<div class="flex flex-col items-center justify-center py-12 gap-4">
				<div class="h-10 w-10 animate-spin rounded-full border-4 border-green-200 border-t-green-600"></div>
				<p class="text-sm text-gray-500 animate-pulse">AI is generating your quiz…</p>
			</div>
		</Card>
	{/if}

</PageLayout>
