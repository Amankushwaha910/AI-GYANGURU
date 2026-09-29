<script lang="ts">
	import { summariesApi } from '$api/summaries';
	import { filesApi } from '$api/files';
	import { toast } from '$stores/toast';
	import { ApiClientError } from '$api/client';
	import { modelSelector } from '$stores/modelSelector';
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import type { Summary, SummarySection, Upload } from '$types';
	import { SECTION_LABELS, formatFileSize } from '$lib/utils';
	import Button from '$components/ui/Button.svelte';
	import Input from '$components/ui/Input.svelte';
	import Card from '$components/ui/Card.svelte';
	import PageLayout from '$components/layout/PageLayout.svelte';
	import ModelSelector from '$components/ui/ModelSelector.svelte';
	import SummaryResult from './SummaryResult.svelte';
	import { BookOpen, Sparkles, FileText, ChevronDown } from 'lucide-svelte';

	const ALL_SECTIONS: SummarySection[] = [
		'definition', 'key_concepts', 'important_facts', 'formula_sheet',
		'mnemonics', 'exam_tips', 'revision_notes', 'checklist'
	];

	// ── State ──────────────────────────────────────────────────────────────────
	let topic = '';
	let selectedSections: SummarySection[] = ['definition', 'key_concepts', 'important_facts', 'revision_notes'];
	let loading = false;
	let result: Summary | null = null;
	let error = '';

	// File source
	let sourceMode: 'topic' | 'file' = 'topic';
	let readyUploads: Upload[] = [];
	let selectedUploadId = '';
	let loadingUploads = false;

	onMount(async () => {
		// Check if navigated here with ?upload_id=... (e.g. from /upload page)
		const urlUploadId = $page.url.searchParams.get('upload_id');

		loadingUploads = true;
		try {
			const res = await filesApi.list({ page: 1, page_size: 50 });
			readyUploads = res.data.filter(u => u.status === 'completed');

			if (urlUploadId && readyUploads.some(u => u.id === urlUploadId)) {
				sourceMode = 'file';
				selectedUploadId = urlUploadId;
			}
		} catch {
			// Non-critical — topic mode still works
		} finally {
			loadingUploads = false;
		}
	});

	// ── Section toggle ─────────────────────────────────────────────────────────
	function toggleSection(s: SummarySection) {
		if (selectedSections.includes(s)) {
			if (selectedSections.length > 1) selectedSections = selectedSections.filter(x => x !== s);
		} else {
			selectedSections = [...selectedSections, s];
		}
	}

	// ── Generate ───────────────────────────────────────────────────────────────
	async function generate() {
		if (sourceMode === 'topic' && !topic.trim()) {
			error = 'Please enter a topic'; return;
		}
		if (sourceMode === 'file' && !selectedUploadId) {
			error = 'Please select an uploaded file'; return;
		}
		if (selectedSections.length === 0) {
			error = 'Select at least one section'; return;
		}
		error = '';
		loading = true;
		result = null;

		const { provider, model } = modelSelector.getSelection();

		try {
			let res;
			if (sourceMode === 'file') {
				res = await summariesApi.generateFromFile({
					upload_id: selectedUploadId,
					sections: selectedSections,
					model,
					provider,
				});
			} else {
				res = await summariesApi.generate({
					topic: topic.trim(),
					sections: selectedSections,
					model,
					provider,
				});
			}
			result = res.data ?? null;
			toast.success('Summary generated!');
		} catch (e: any) {
			error = e instanceof ApiClientError ? e.message : 'Generation failed. Please try again.';
			toast.error(error);
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head><title>Summary — AI GyanGuru</title></svelte:head>

<PageLayout title="AI Summary" subtitle="Generate structured revision notes for any topic or uploaded document">

	<!-- ── Input card (full width) ──────────────────────────────────────────── -->
	<Card padding="lg" class="mb-6">
		<div class="flex items-center gap-3 mb-6">
			<div class="h-9 w-9 rounded-xl bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center flex-shrink-0">
				<BookOpen class="h-5 w-5 text-blue-600 dark:text-blue-400" />
			</div>
			<div>
				<h2 class="font-semibold text-gray-900 dark:text-white">Generate Summary</h2>
				<p class="text-xs text-gray-500 dark:text-gray-400">Enter a topic or pick an uploaded document</p>
			</div>
		</div>

		<form on:submit|preventDefault={generate} class="space-y-5">

			<!-- Source mode tabs -->
			<div class="flex gap-1 rounded-xl bg-gray-100 dark:bg-gray-800 p-1 w-fit">
				<button
					type="button"
					on:click={() => { sourceMode = 'topic'; error = ''; }}
					class="rounded-lg px-4 py-1.5 text-sm font-medium transition-all
					       {sourceMode === 'topic'
					         ? 'bg-white dark:bg-gray-900 text-gray-900 dark:text-white shadow-sm'
					         : 'text-gray-500 dark:text-gray-400 hover:text-gray-700'}"
				>
					Topic
				</button>
				<button
					type="button"
					on:click={() => { sourceMode = 'file'; error = ''; }}
					class="rounded-lg px-4 py-1.5 text-sm font-medium transition-all
					       {sourceMode === 'file'
					         ? 'bg-white dark:bg-gray-900 text-gray-900 dark:text-white shadow-sm'
					         : 'text-gray-500 dark:text-gray-400 hover:text-gray-700'}"
				>
					Uploaded File
				</button>
			</div>

			<!-- Topic input OR file selector -->
			{#if sourceMode === 'topic'}
				<Input
					label="Topic"
					placeholder="e.g. Newton's Laws of Motion"
					bind:value={topic}
					error={error && !topic ? error : ''}
					required
				/>
			{:else}
				<div>
					<label for="file-select-summary" class="text-sm font-medium text-gray-700 dark:text-gray-300 block mb-1.5">
						Select Uploaded File
					</label>
					{#if loadingUploads}
						<p class="text-sm text-gray-400">Loading your files…</p>
					{:else if readyUploads.length === 0}
						<p class="text-sm text-gray-500 dark:text-gray-400">
							No processed files yet.
							<a href="/upload" class="text-brand-600 dark:text-brand-400 hover:underline font-medium">Upload a file</a>
							first.
						</p>
					{:else}
						<div class="relative">
							<select
								id="file-select-summary"
								bind:value={selectedUploadId}
								class="w-full h-10 rounded-xl border border-gray-300 dark:border-gray-700
								       bg-white dark:bg-gray-900 px-4 pr-9 text-sm text-gray-900
								       dark:text-gray-100 focus:outline-none focus:ring-2
								       focus:ring-brand-500 appearance-none"
							>
								<option value="">— Choose a file —</option>
								{#each readyUploads as u}
									<option value={u.id}>
										{u.original_filename} ({formatFileSize(u.file_size_bytes)})
									</option>
								{/each}
							</select>
							<ChevronDown class="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
						</div>
					{/if}
					{#if error && !selectedUploadId}
						<p class="text-xs text-red-600 dark:text-red-400 mt-1">{error}</p>
					{/if}
				</div>
			{/if}

			<!-- AI Model -->
			<div>
				<p class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">AI Model</p>
				<ModelSelector />
			</div>

			<!-- Section selector -->
			<div>
				<p class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Include Sections</p>
				<div class="flex flex-wrap gap-2">
					{#each ALL_SECTIONS as section}
						<button
							type="button"
							on:click={() => toggleSection(section)}
							class="rounded-lg px-3 py-1.5 text-xs font-medium border transition-all {
								selectedSections.includes(section)
									? 'bg-brand-600 text-white border-brand-600 dark:bg-brand-500 dark:border-brand-500'
									: 'bg-white text-gray-600 border-gray-300 hover:border-brand-400 dark:bg-gray-800 dark:text-gray-400 dark:border-gray-700'
							}"
						>
							{SECTION_LABELS[section]}
						</button>
					{/each}
				</div>
			</div>

			{#if error && ((sourceMode === 'topic' && topic) || sourceMode === 'file')}
				<p class="text-sm text-red-600 dark:text-red-400">{error}</p>
			{/if}

			<div class="flex items-center gap-3">
				<Button type="submit" {loading} disabled={loading} size="lg">
					<Sparkles class="h-4 w-4" />
					{loading ? 'Generating…' : 'Generate Summary'}
				</Button>
				{#if result}
					<button
						type="button"
						on:click={() => { result = null; topic = ''; selectedUploadId = ''; }}
						class="text-sm text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
					>
						Clear
					</button>
				{/if}
			</div>
		</form>
	</Card>

	<!-- ── Pro tip ───────────────────────────────────────────────────────────── -->
	{#if !result && !loading}
		<div class="mb-6 rounded-xl bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800 p-4">
			<p class="text-sm font-medium text-blue-700 dark:text-blue-300 mb-1">💡 Pro Tip</p>
			<p class="text-xs text-blue-600 dark:text-blue-400 leading-relaxed">
				Be specific with your topic for better results. "Photosynthesis Light Reactions" works better than "Biology".
				For uploaded files, the AI reads the actual document content — not just the filename.
			</p>
		</div>
	{/if}

	<!-- ── Result (full width, below input) ─────────────────────────────────── -->
	{#if loading}
		<Card padding="lg">
			<div class="flex flex-col items-center justify-center py-12 gap-4">
				<div class="h-10 w-10 animate-spin rounded-full border-4 border-brand-200 border-t-brand-600"></div>
				<p class="text-sm text-gray-500 dark:text-gray-400 animate-pulse">AI is generating your summary…</p>
			</div>
		</Card>
	{:else if result}
		<SummaryResult summary={result} />
	{/if}

</PageLayout>
