<script lang="ts">
	import { explanationsApi } from '$api/explanations';
	import { filesApi } from '$api/files';
	import { toast } from '$stores/toast';
	import { ApiClientError } from '$api/client';
	import { modelSelector } from '$stores/modelSelector';
	import { onMount } from 'svelte';
	import type { Explanation, Upload } from '$types';
	import { EXPLANATION_SECTION_LABELS, formatFileSize } from '$lib/utils';
	import Button from '$components/ui/Button.svelte';
	import Input from '$components/ui/Input.svelte';
	import Card from '$components/ui/Card.svelte';
	import PageLayout from '$components/layout/PageLayout.svelte';
	import ModelSelector from '$components/ui/ModelSelector.svelte';
	import { Lightbulb, Sparkles, ChevronDown, ChevronUp, Copy, Check } from 'lucide-svelte';
	import { page } from '$app/stores';

	// ── State ──────────────────────────────────────────────────────────────────
	let topic = '';
	let loading = false;
	let result: Explanation | null = null;
	let error = '';

	let sourceMode: 'topic' | 'file' = 'topic';
	let readyUploads: Upload[] = [];
	let selectedUploadId = '';
	let loadingUploads = false;

	const ORDERED_SECTIONS = [
		'introduction', 'step_by_step', 'concept_breakdown', 'real_examples',
		'analogies', 'practical_applications', 'common_mistakes', 'faqs', 'final_recap'
	];

	let collapsed: Record<string, boolean> = {};
	let copied: Record<string, boolean> = {};

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

	function toggle(key: string) {
		collapsed[key] = !collapsed[key];
		collapsed = { ...collapsed };
	}

	async function copySection(key: string, text: string) {
		await navigator.clipboard.writeText(text);
		copied[key] = true;
		copied = { ...copied };
		setTimeout(() => { copied[key] = false; copied = { ...copied }; }, 2000);
	}

	function formatContent(text: string): string {
		return text.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
	}

	async function generate() {
		if (sourceMode === 'topic' && !topic.trim()) { error = 'Please enter a topic'; return; }
		if (sourceMode === 'file' && !selectedUploadId) { error = 'Please select an uploaded file'; return; }
		error = '';
		loading = true;
		result = null;

		const { provider, model } = modelSelector.getSelection();

		try {
			let res;
			if (sourceMode === 'file') {
				res = await explanationsApi.generateFromFile({
					upload_id: selectedUploadId,
					model,
					provider,
				});
			} else {
				res = await explanationsApi.generate({ topic: topic.trim(), model, provider });
			}
			result = res.data ?? null;
			toast.success('Explanation ready!');
		} catch (e: any) {
			error = e instanceof ApiClientError ? e.message : 'Generation failed. Please try again.';
			toast.error(error);
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head><title>Explanation — AI GyanGuru</title></svelte:head>

<PageLayout title="AI Explanation" subtitle="Get deep, structured explanations for any concept or uploaded document">

	<!-- ── Input card (full width) ──────────────────────────────────────────── -->
	<Card padding="lg" class="mb-6">
		<div class="flex items-center gap-3 mb-6">
			<div class="h-9 w-9 rounded-xl bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center flex-shrink-0">
				<Lightbulb class="h-5 w-5 text-purple-600 dark:text-purple-400" />
			</div>
			<div>
				<h2 class="font-semibold text-gray-900 dark:text-white">Explain a Concept</h2>
				<p class="text-xs text-gray-500 dark:text-gray-400">
					You'll get: Introduction → Step-by-step → Examples → Analogies → Applications → Mistakes → FAQs → Recap
				</p>
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

			{#if sourceMode === 'topic'}
				<Input
					label="Concept or Topic"
					placeholder="e.g. Recursion in Programming"
					bind:value={topic}
					error={error && !topic ? error : ''}
					required
				/>
			{:else}
				<div>
					<label for="file-select-explanation" class="text-sm font-medium text-gray-700 dark:text-gray-300 block mb-1.5">Select Uploaded File</label>
					{#if loadingUploads}
						<p class="text-sm text-gray-400">Loading your files…</p>
					{:else if readyUploads.length === 0}
						<p class="text-sm text-gray-500 dark:text-gray-400">
							No processed files yet.
							<a href="/upload" class="text-brand-600 dark:text-brand-400 hover:underline font-medium">Upload a file</a> first.
						</p>
					{:else}
						<div class="relative">
							<select id="file-select-explanation" bind:value={selectedUploadId}
								class="w-full h-10 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 px-4 pr-9 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-500 appearance-none">
								<option value="">— Choose a file —</option>
								{#each readyUploads as u}
									<option value={u.id}>{u.original_filename} ({formatFileSize(u.file_size_bytes)})</option>
								{/each}
							</select>
							<ChevronDown class="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
						</div>
					{/if}
					{#if error && !selectedUploadId}<p class="text-xs text-red-600 dark:text-red-400 mt-1">{error}</p>{/if}
				</div>
			{/if}

			<!-- AI Model -->
			<div>
				<p class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">AI Model</p>
				<ModelSelector />
			</div>

			{#if error && ((sourceMode === 'topic' && topic) || sourceMode === 'file')}
				<p class="text-sm text-red-600 dark:text-red-400">{error}</p>
			{/if}

			<div class="flex items-center gap-3">
				<Button type="submit" {loading} disabled={loading} size="lg" variant="primary">
					<Sparkles class="h-4 w-4" />
					{loading ? 'Generating…' : 'Explain This'}
				</Button>
				{#if result}
					<button type="button" on:click={() => { result = null; topic = ''; selectedUploadId = ''; }}
						class="text-sm text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors">
						Clear
					</button>
				{/if}
			</div>
		</form>
	</Card>

	<!-- ── Result (full width, below input) ─────────────────────────────────── -->
	{#if loading}
		<Card padding="lg">
			<div class="flex flex-col items-center justify-center py-12 gap-4">
				<div class="h-10 w-10 animate-spin rounded-full border-4 border-purple-200 border-t-purple-600"></div>
				<p class="text-sm text-gray-500 animate-pulse">AI is building your explanation…</p>
			</div>
		</Card>

	{:else if result}
		<!-- Result header -->
		<Card padding="md" class="mb-4">
			<h2 class="text-lg font-bold text-gray-900 dark:text-white mb-1">{result.topic}</h2>
			<p class="text-sm text-gray-400">Full explanation · {result.model_used}</p>
		</Card>

		<!-- Sections (accordion) -->
		{#each ORDERED_SECTIONS as sectionKey}
			{@const content = result.content[sectionKey] ?? ''}
			{#if content}
				<Card padding="none" class="mb-3">
					<button
						class="flex w-full items-center justify-between px-5 py-4 text-left"
						on:click={() => toggle(sectionKey)}
					>
						<span class="font-semibold text-sm text-gray-900 dark:text-white">
							{EXPLANATION_SECTION_LABELS[sectionKey] ?? sectionKey}
						</span>
						<div class="flex items-center gap-2">
							<button
								on:click|stopPropagation={() => copySection(sectionKey, content)}
								class="rounded-lg p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
							>
								{#if copied[sectionKey]}
									<Check class="h-3.5 w-3.5 text-green-500" />
								{:else}
									<Copy class="h-3.5 w-3.5" />
								{/if}
							</button>
							{#if collapsed[sectionKey]}
								<ChevronDown class="h-4 w-4 text-gray-400" />
							{:else}
								<ChevronUp class="h-4 w-4 text-gray-400" />
							{/if}
						</div>
					</button>
					{#if !collapsed[sectionKey]}
						<div class="px-5 pb-5 border-t border-gray-100 dark:border-gray-800 pt-4">
							<div class="prose prose-sm dark:prose-invert max-w-none text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
								{@html formatContent(content)}
							</div>
						</div>
					{/if}
				</Card>
			{/if}
		{/each}
	{/if}

</PageLayout>
