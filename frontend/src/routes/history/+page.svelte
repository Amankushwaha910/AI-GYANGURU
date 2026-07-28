<script lang="ts">
	import { onMount } from 'svelte';
	import { historyApi } from '$api/history';
	import { toast } from '$stores/toast';
	import type { HistoryItem, HistoryItemType } from '$types';
	import { formatRelativeTime, HISTORY_TYPE_COLORS, HISTORY_TYPE_LABELS } from '$lib/utils';
	import Button from '$components/ui/Button.svelte';
	import Card from '$components/ui/Card.svelte';
	import Skeleton from '$components/ui/Skeleton.svelte';
	import Input from '$components/ui/Input.svelte';
	import EmptyState from '$components/ui/EmptyState.svelte';
	import PageLayout from '$components/layout/PageLayout.svelte';
	import { Clock, Trash2, Search } from 'lucide-svelte';

	let items: HistoryItem[] = [];
	let total = 0;
	let loading = true;
	let page = 1;
	const pageSize = 20;
	let search = '';
	let activeType: HistoryItemType | '' = '';
	let deletingId: string | null = null;

	const typeFilters: { value: HistoryItemType | ''; label: string }[] = [
		{ value: '', label: 'All' },
		{ value: 'summary', label: 'Summaries' },
		{ value: 'explanation', label: 'Explanations' },
		{ value: 'quiz', label: 'Quizzes' },
		{ value: 'upload', label: 'Uploads' }
	];

	async function load() {
		loading = true;
		try {
			const res = await historyApi.list({
				page,
				page_size: pageSize,
				item_type: activeType || undefined,
				search: search || undefined
			});
			items = res.data;
			total = res.total;
		} finally { loading = false; }
	}

	onMount(() => load());

	async function handleDelete(id: string) {
		deletingId = id;
		try {
			await historyApi.delete(id);
			items = items.filter(i => i.id !== id);
			toast.success('Item removed from history');
		} catch { toast.error('Failed to delete item'); }
		finally { deletingId = null; }
	}

	function handleSearch() { page = 1; load(); }
	function setType(t: HistoryItemType | '') { activeType = t; page = 1; load(); }
	$: totalPages = Math.ceil(total / pageSize);
</script>

<svelte:head><title>History — AI GyanGuru</title></svelte:head>

<PageLayout title="History" subtitle="Browse all your past learning activities">
	<!-- Filters -->
	<div class="flex flex-col sm:flex-row gap-3 mb-6">
		<div class="flex flex-wrap gap-2">
			{#each typeFilters as tf}
				<button
					on:click={() => setType(tf.value)}
					class="rounded-xl px-3 py-1.5 text-sm font-medium border transition-all {
						activeType === tf.value
							? 'bg-brand-600 text-white border-brand-600'
							: 'bg-white dark:bg-gray-900 text-gray-600 dark:text-gray-400 border-gray-200 dark:border-gray-700 hover:border-brand-400'
					}"
				>{tf.label}</button>
			{/each}
		</div>
		<div class="flex gap-2 sm:ml-auto">
			<div class="relative">
				<Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
				<input
					class="h-9 pl-9 pr-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
					placeholder="Search by topic..."
					bind:value={search}
					on:keydown={(e) => e.key === 'Enter' && handleSearch()}
				/>
			</div>
			<Button variant="secondary" size="sm" on:click={handleSearch}>Search</Button>
		</div>
	</div>

	<!-- Items -->
	{#if loading}
		<div class="space-y-3">
			{#each Array(8) as _}
				<div class="flex gap-4 p-4 rounded-xl border border-gray-100 dark:border-gray-800 bg-white dark:bg-gray-900">
					<Skeleton height="h-10" width="w-10" rounded="rounded-xl" />
					<div class="flex-1 space-y-2">
						<Skeleton height="h-4" width="w-2/3" />
						<Skeleton height="h-3" width="w-1/4" />
					</div>
				</div>
			{/each}
		</div>
	{:else if items.length === 0}
		<EmptyState icon={Clock} title="No history yet" description="Start learning and your activity will appear here." />
	{:else}
		<div class="space-y-2">
			{#each items as item (item.id)}
				<div class="flex items-center gap-4 p-4 rounded-xl border border-gray-100 dark:border-gray-800 bg-white dark:bg-gray-900 hover:shadow-sm transition-shadow group">
					<span class="inline-flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl text-sm font-bold {HISTORY_TYPE_COLORS[item.item_type]}">
						{HISTORY_TYPE_LABELS[item.item_type][0]}
					</span>
					<div class="flex-1 min-w-0">
						<p class="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">{item.topic}</p>
						<p class="text-xs text-gray-400 dark:text-gray-500">
							{HISTORY_TYPE_LABELS[item.item_type]} · {formatRelativeTime(item.created_at)}
						</p>
					</div>
					<button
						on:click={() => handleDelete(item.id)}
						disabled={deletingId === item.id}
						class="opacity-0 group-hover:opacity-100 rounded-lg p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-all"
						title="Delete"
					>
						<Trash2 class="h-4 w-4" />
					</button>
				</div>
			{/each}
		</div>

		<!-- Pagination -->
		{#if totalPages > 1}
			<div class="flex items-center justify-between mt-6">
				<p class="text-sm text-gray-500 dark:text-gray-400">
					{(page - 1) * pageSize + 1}–{Math.min(page * pageSize, total)} of {total}
				</p>
				<div class="flex gap-2">
					<Button variant="secondary" size="sm" disabled={page === 1} on:click={() => { page--; load(); }}>← Prev</Button>
					<Button variant="secondary" size="sm" disabled={page >= totalPages} on:click={() => { page++; load(); }}>Next →</Button>
				</div>
			</div>
		{/if}
	{/if}
</PageLayout>
