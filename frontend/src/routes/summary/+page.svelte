<script lang="ts">
	import { summariesApi } from '$api/summaries';
	import { toast } from '$stores/toast';
	import { ApiClientError } from '$api/client';
	import type { Summary, SummarySection } from '$types';
	import { SECTION_LABELS } from '$lib/utils';
	import Button from '$components/ui/Button.svelte';
	import Input from '$components/ui/Input.svelte';
	import Card from '$components/ui/Card.svelte';
	import PageLayout from '$components/layout/PageLayout.svelte';
	import SummaryResult from './SummaryResult.svelte';
	import { BookOpen, Sparkles } from 'lucide-svelte';

	const ALL_SECTIONS: SummarySection[] = [
		'definition','key_concepts','important_facts','formula_sheet',
		'mnemonics','exam_tips','revision_notes','checklist'
	];

	let topic = '';
	let selectedSections: SummarySection[] = ['definition','key_concepts','important_facts','revision_notes'];
	let loading = false;
	let result: Summary | null = null;
	let error = '';

	function toggleSection(s: SummarySection) {
		if (selectedSections.includes(s)) {
			if (selectedSections.length > 1) selectedSections = selectedSections.filter(x => x !== s);
		} else {
			selectedSections = [...selectedSections, s];
		}
	}

	async function generate() {
		if (!topic.trim()) { error = 'Please enter a topic'; return; }
		if (selectedSections.length === 0) { error = 'Select at least one section'; return; }
		error = '';
		loading = true;
		result = null;

		try {
			const res = await summariesApi.generate({ topic: topic.trim(), sections: selectedSections });
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

<PageLayout title="AI Summary" subtitle="Generate structured revision notes for any topic">
	<div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
		<!-- Input panel -->
		<div class="xl:col-span-1 space-y-5">
			<Card padding="md">
				<div class="flex items-center gap-2 mb-5">
					<div class="h-8 w-8 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
						<BookOpen class="h-4 w-4 text-blue-600 dark:text-blue-400" />
					</div>
					<h2 class="font-semibold text-gray-900 dark:text-white">Generate Summary</h2>
				</div>

				<form on:submit|preventDefault={generate} class="space-y-5">
					<Input
						label="Topic"
						placeholder="e.g. Newton's Laws of Motion"
						bind:value={topic}
						error={error && !topic ? error : ''}
						required
					/>

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

					{#if error && topic}
						<p class="text-sm text-red-600 dark:text-red-400">{error}</p>
					{/if}

					<Button type="submit" {loading} disabled={loading} class="w-full">
						<Sparkles class="h-4 w-4" />
						{loading ? 'Generating...' : 'Generate Summary'}
					</Button>
				</form>
			</Card>

			<!-- Tip card -->
			<div class="rounded-xl bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800 p-4">
				<p class="text-sm font-medium text-blue-700 dark:text-blue-300 mb-1">💡 Pro Tip</p>
				<p class="text-xs text-blue-600 dark:text-blue-400 leading-relaxed">
					Be specific with your topic for better results. "Photosynthesis Light Reactions" works better than "Biology".
				</p>
			</div>
		</div>

		<!-- Result panel -->
		<div class="xl:col-span-2">
			{#if loading}
				<Card padding="md">
					<div class="flex flex-col items-center justify-center py-16 gap-4">
						<div class="h-10 w-10 animate-spin rounded-full border-4 border-brand-200 border-t-brand-600"></div>
						<p class="text-sm text-gray-500 dark:text-gray-400 animate-pulse">AI is generating your summary...</p>
					</div>
				</Card>
			{:else if result}
				<SummaryResult summary={result} />
			{:else}
				<Card padding="md">
					<div class="flex flex-col items-center justify-center py-20">
						<div class="h-16 w-16 rounded-2xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center mb-4">
							<BookOpen class="h-8 w-8 text-gray-300 dark:text-gray-600" />
						</div>
						<p class="text-base font-medium text-gray-500 dark:text-gray-400">Your summary will appear here</p>
						<p class="text-sm text-gray-400 dark:text-gray-500 mt-1">Enter a topic and click Generate</p>
					</div>
				</Card>
			{/if}
		</div>
	</div>
</PageLayout>
