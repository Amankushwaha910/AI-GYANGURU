<script lang="ts">
	import { onMount } from 'svelte';
	import { analyticsApi } from '$api/analytics';
	import type { AnalyticsDashboard } from '$types';
	import Card from '$components/ui/Card.svelte';
	import Skeleton from '$components/ui/Skeleton.svelte';
	import PageLayout from '$components/layout/PageLayout.svelte';
	import { Target, BookOpen, HelpCircle, TrendingUp, TrendingDown, BarChart2 } from 'lucide-svelte';

	let dashboard: AnalyticsDashboard | null = null;
	let loading = true;

	onMount(async () => {
		try {
			const res = await analyticsApi.getDashboard();
			dashboard = res.data ?? null;
		} finally { loading = false; }
	});

	const statCards = [
		{ key: 'total_topics_studied', label: 'Topics Studied', icon: Target, color: 'bg-blue-500' },
		{ key: 'total_summaries_generated', label: 'Summaries', icon: BookOpen, color: 'bg-purple-500' },
		{ key: 'total_quizzes_taken', label: 'Quizzes Taken', icon: HelpCircle, color: 'bg-green-500' },
		{ key: 'overall_quiz_accuracy', label: 'Quiz Accuracy', icon: TrendingUp, color: 'bg-brand-500', suffix: '%' }
	];

	function getStatValue(key: string): number {
		if (!dashboard) return 0;
		return (dashboard.summary as unknown as Record<string, number>)[key] ?? 0;
	}
</script>

<svelte:head><title>Analytics — AI GyanGuru</title></svelte:head>

<PageLayout title="Analytics" subtitle="Track your learning progress and performance">
	<!-- Stats -->
	<div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
		{#each statCards as stat}
			<Card padding="md">
				{#if loading}
					<Skeleton height="h-16" />
				{:else}
					<div class="flex items-start justify-between">
						<div>
							<p class="text-xs font-medium text-gray-500 dark:text-gray-400">{stat.label}</p>
							<p class="mt-1 text-3xl font-bold text-gray-900 dark:text-white">
								{getStatValue(stat.key)}{stat.suffix ?? ''}
							</p>
						</div>
						<div class="h-9 w-9 rounded-xl {stat.color} flex items-center justify-center">
							<svelte:component this={stat.icon} class="h-4.5 w-4.5 text-white" />
						</div>
					</div>
				{/if}
			</Card>
		{/each}
	</div>

	<!-- Charts row -->
	<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
		<!-- Daily activity bar chart -->
		<Card padding="md">
			<h3 class="text-sm font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
				<BarChart2 class="h-4 w-4 text-gray-400" /> Daily Activity (Last 30 Days)
			</h3>
			{#if loading}
				<Skeleton height="h-36" />
			{:else if dashboard?.daily_activity?.length}
				<div class="flex items-end gap-1 h-36">
					{#each dashboard.daily_activity as day}
						{@const max = Math.max(...dashboard.daily_activity.map(d => d.count), 1)}
						<div
							class="flex-1 rounded-t-sm bg-brand-500 dark:bg-brand-400 min-h-[4px] transition-all hover:opacity-80"
							style="height: {Math.max((day.count / max) * 100, 4)}%"
							title="{day.date}: {day.count} activities"
						></div>
					{/each}
				</div>
			{:else}
				<p class="text-sm text-gray-400 text-center py-10">No activity data yet.</p>
			{/if}
		</Card>

		<!-- Quiz accuracy trend -->
		<Card padding="md">
			<h3 class="text-sm font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
				<TrendingUp class="h-4 w-4 text-gray-400" /> Quiz Accuracy Trend (Last 30 Days)
			</h3>
			{#if loading}
				<Skeleton height="h-36" />
			{:else if dashboard?.quiz_accuracy_trend?.length}
				<div class="flex items-end gap-1 h-36">
					{#each dashboard.quiz_accuracy_trend as day}
						<div
							class="flex-1 rounded-t-sm bg-green-500 dark:bg-green-400 min-h-[4px] transition-all hover:opacity-80"
							style="height: {Math.max(day.count, 4)}%"
							title="{day.date}: {day.count}%"
						></div>
					{/each}
				</div>
			{:else}
				<p class="text-sm text-gray-400 text-center py-10">Complete some quizzes to see trends.</p>
			{/if}
		</Card>
	</div>

	<!-- Weak / Strong areas -->
	<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
		<Card padding="md">
			<h3 class="text-sm font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
				<TrendingDown class="h-4 w-4 text-red-400" /> Weak Areas
			</h3>
			{#if loading}
				<div class="space-y-2">{#each Array(3) as _}<Skeleton height="h-10" />{/each}</div>
			{:else if dashboard?.weak_areas?.length}
				{#each dashboard.weak_areas as area}
					<div class="mb-3">
						<div class="flex justify-between text-sm mb-1">
							<span class="text-gray-700 dark:text-gray-300 font-medium">{area.category}</span>
							<span class="text-red-600 dark:text-red-400 font-bold">{area.accuracy}%</span>
						</div>
						<div class="h-2 rounded-full bg-gray-100 dark:bg-gray-800">
							<div class="h-2 rounded-full bg-red-400 transition-all" style="width: {area.accuracy}%"></div>
						</div>
					</div>
				{/each}
			{:else}
				<p class="text-sm text-gray-400 text-center py-6">No data yet. Take some quizzes!</p>
			{/if}
		</Card>

		<Card padding="md">
			<h3 class="text-sm font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
				<TrendingUp class="h-4 w-4 text-green-400" /> Strong Areas
			</h3>
			{#if loading}
				<div class="space-y-2">{#each Array(3) as _}<Skeleton height="h-10" />{/each}</div>
			{:else if dashboard?.strong_areas?.length}
				{#each dashboard.strong_areas as area}
					<div class="mb-3">
						<div class="flex justify-between text-sm mb-1">
							<span class="text-gray-700 dark:text-gray-300 font-medium">{area.category}</span>
							<span class="text-green-600 dark:text-green-400 font-bold">{area.accuracy}%</span>
						</div>
						<div class="h-2 rounded-full bg-gray-100 dark:bg-gray-800">
							<div class="h-2 rounded-full bg-green-400 transition-all" style="width: {area.accuracy}%"></div>
						</div>
					</div>
				{/each}
			{:else}
				<p class="text-sm text-gray-400 text-center py-6">No data yet.</p>
			{/if}
		</Card>
	</div>

	<!-- Activity Heatmap -->
	<Card padding="md">
		<h3 class="text-sm font-semibold text-gray-900 dark:text-white mb-4">Activity Heatmap (Last 90 Days)</h3>
		{#if loading}
			<Skeleton height="h-16" />
		{:else if dashboard?.activity_heatmap?.length}
			<div class="flex flex-wrap gap-1">
				{#each dashboard.activity_heatmap as day}
					{@const intensity = Math.min(day.count, 5)}
					<div
						class="h-4 w-4 rounded-sm transition-all cursor-default"
						class:bg-gray-100={intensity === 0}
						class:dark:bg-gray-800={intensity === 0}
						class:bg-brand-200={intensity === 1}
						class:bg-brand-300={intensity === 2}
						class:bg-brand-400={intensity === 3}
						class:bg-brand-500={intensity === 4}
						class:bg-brand-600={intensity >= 5}
						title="{day.date}: {day.count} activities"
					></div>
				{/each}
			</div>
		{:else}
			<p class="text-sm text-gray-400 text-center py-6">No activity to display.</p>
		{/if}
	</Card>
</PageLayout>
