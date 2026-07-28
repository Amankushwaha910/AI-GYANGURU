<script lang="ts">
	import { explanationsApi } from '$api/explanations';
	import { toast } from '$stores/toast';
	import { ApiClientError } from '$api/client';
	import type { Explanation } from '$types';
	import { EXPLANATION_SECTION_LABELS } from '$lib/utils';
	import Button from '$components/ui/Button.svelte';
	import Input from '$components/ui/Input.svelte';
	import Card from '$components/ui/Card.svelte';
	import PageLayout from '$components/layout/PageLayout.svelte';
	import { Lightbulb, Sparkles, ChevronDown, ChevronUp, Copy, Check } from 'lucide-svelte';

	let topic = '';
	let loading = false;
	let result: Explanation | null = null;
	let error = '';

	const ORDERED_SECTIONS = [
		'introduction','step_by_step','concept_breakdown','real_examples',
		'analogies','practical_applications','common_mistakes','faqs','final_recap'
	];

	let collapsed: Record<string, boolean> = {};
	let copied: Record<string, boolean> = {};

	function toggle(key: string) { collapsed[key] = !collapsed[key]; collapsed = { ...collapsed }; }

	async function copySection(key: string, text: string) {
		await navigator.clipboard.writeText(text);
		copied[key] = true; copied = { ...copied };
		setTimeout(() => { copied[key] = false; copied = { ...copied }; }, 2000);
	}

	function formatContent(text: string): string {
		return text.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
	}

	async function generate() {
		if (!topic.trim()) { error = 'Please enter a topic'; return; }
		error = ''; loading = true; result = null;
		try {
			const res = await explanationsApi.generate({ topic: topic.trim() });
			result = res.data ?? null;
			toast.success('Explanation ready!');
		} catch (e: any) {
			error = e instanceof ApiClientError ? e.message : 'Generation failed. Please try again.';
			toast.error(error);
		} finally { loading = false; }
	}
</script>

<svelte:head><title>Explanation — AI GyanGuru</title></svelte:head>

<PageLayout title="AI Explanation" subtitle="Get deep, structured explanations for any concept">
	<div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
		<!-- Input -->
		<div class="xl:col-span-1 space-y-5">
			<Card padding="md">
				<div class="flex items-center gap-2 mb-5">
					<div class="h-8 w-8 rounded-lg bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
						<Lightbulb class="h-4 w-4 text-purple-600 dark:text-purple-400" />
					</div>
					<h2 class="font-semibold text-gray-900 dark:text-white">Explain a Concept</h2>
				</div>
				<form on:submit|preventDefault={generate} class="space-y-5">
					<Input
						label="Concept or Topic"
						placeholder="e.g. Recursion in Programming"
						bind:value={topic}
						error={error}
						required
					/>
					<div class="rounded-xl bg-purple-50 dark:bg-purple-900/20 border border-purple-100 dark:border-purple-800 p-3">
						<p class="text-xs text-purple-600 dark:text-purple-400">
							You'll get: Introduction → Step-by-step → Examples → Analogies → Applications → Mistakes → FAQs → Recap
						</p>
					</div>
					<Button type="submit" {loading} disabled={loading} class="w-full" variant="primary">
						<Sparkles class="h-4 w-4" />
						{loading ? 'Generating...' : 'Explain This'}
					</Button>
				</form>
			</Card>
		</div>

		<!-- Result -->
		<div class="xl:col-span-2 space-y-4">
			{#if loading}
				<Card padding="md">
					<div class="flex flex-col items-center justify-center py-16 gap-4">
						<div class="h-10 w-10 animate-spin rounded-full border-4 border-purple-200 border-t-purple-600"></div>
						<p class="text-sm text-gray-500 animate-pulse">AI is building your explanation...</p>
					</div>
				</Card>
			{:else if result}
				<Card padding="md">
					<h2 class="text-lg font-bold text-gray-900 dark:text-white mb-1">{result.topic}</h2>
					<p class="text-sm text-gray-400 mb-4">Full explanation · {result.model_used}</p>
				</Card>

				{#each ORDERED_SECTIONS as sectionKey}
					{@const content = result.content[sectionKey] ?? ''}
					{#if content}
						<Card padding="none">
							<button class="flex w-full items-center justify-between px-5 py-4" on:click={() => toggle(sectionKey)}>
								<span class="font-semibold text-sm text-gray-900 dark:text-white">
									{EXPLANATION_SECTION_LABELS[sectionKey] ?? sectionKey}
								</span>
								<div class="flex items-center gap-2">
									<button on:click|stopPropagation={() => copySection(sectionKey, content)}
										class="rounded-lg p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
										{#if copied[sectionKey]}<Check class="h-3.5 w-3.5 text-green-500" />
										{:else}<Copy class="h-3.5 w-3.5" />{/if}
									</button>
									{#if collapsed[sectionKey]}<ChevronDown class="h-4 w-4 text-gray-400" />
									{:else}<ChevronUp class="h-4 w-4 text-gray-400" />{/if}
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
			{:else}
				<Card padding="md">
					<div class="flex flex-col items-center justify-center py-20">
						<div class="h-16 w-16 rounded-2xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center mb-4">
							<Lightbulb class="h-8 w-8 text-gray-300 dark:text-gray-600" />
						</div>
						<p class="text-base font-medium text-gray-500 dark:text-gray-400">Your explanation will appear here</p>
					</div>
				</Card>
			{/if}
		</div>
	</div>
</PageLayout>
