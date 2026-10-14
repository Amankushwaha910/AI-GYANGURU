<script lang="ts">
	import type { Summary } from '$types';
	import { SECTION_LABELS } from '$lib/utils';
	import { formatAiContent } from '$lib/formatAiContent.mjs';
	import Card from '$components/ui/Card.svelte';
	import Badge from '$components/ui/Badge.svelte';
	import { ChevronDown, ChevronUp, Copy, Check } from 'lucide-svelte';

	export let summary: Summary;

	// Track collapsed state per section
	let collapsed: Record<string, boolean> = {};
	let copied: Record<string, boolean> = {};

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

</script>

<div class="space-y-4">
	<!-- Header -->
	<Card padding="md">
		<div class="flex items-start justify-between flex-wrap gap-3">
			<div>
				<h2 class="text-lg font-bold text-gray-900 dark:text-white">{summary.topic}</h2>
				<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
					{summary.sections_requested.length} sections · {summary.word_count ?? '—'} words · {summary.model_used}
				</p>
			</div>
			<div class="flex flex-wrap gap-2">
				{#each summary.sections_requested as s}
					<Badge variant="info">{SECTION_LABELS[s] ?? s}</Badge>
				{/each}
			</div>
		</div>
	</Card>

	<!-- Sections -->
	{#each summary.sections_requested as sectionKey}
		{@const content = summary.content[sectionKey] ?? ''}
		{#if content}
			<Card padding="none">
				<div class="flex w-full items-center px-5 py-4 gap-2">
					<button type="button" aria-expanded={!collapsed[sectionKey]} class="flex min-w-0 flex-1 items-center justify-between text-left" on:click={() => toggle(sectionKey)}>
						<span class="font-semibold text-gray-900 dark:text-white text-sm">
							{SECTION_LABELS[sectionKey] ?? sectionKey}
						</span>
						{#if collapsed[sectionKey]}
							<ChevronDown class="h-4 w-4 text-gray-400" />
						{:else}
							<ChevronUp class="h-4 w-4 text-gray-400" />
						{/if}
					</button>
					<button type="button" aria-label="Copy section" on:click={() => copySection(sectionKey, content)}
						class="rounded-lg p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
						title="Copy section">
						{#if copied[sectionKey]}
							<Check class="h-3.5 w-3.5 text-green-500" />
						{:else}
							<Copy class="h-3.5 w-3.5" />
						{/if}
					</button>
				</div>

				{#if !collapsed[sectionKey]}
					<div class="px-5 pb-5 border-t border-gray-100 dark:border-gray-800 pt-4">
						<div
							class="prose prose-sm dark:prose-invert max-w-none text-gray-700 dark:text-gray-300 leading-relaxed text-sm"
						><!-- eslint-disable-next-line svelte/no-at-html-tags -- formatter escapes provider text and only adds fixed formatting tags. -->
							{@html formatAiContent(content, true)}</div>
					</div>
				{/if}
			</Card>
		{/if}
	{/each}
</div>
