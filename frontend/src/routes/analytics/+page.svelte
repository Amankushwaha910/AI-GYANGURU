<script lang="ts">
	import { onMount } from 'svelte';
	import { analyticsApi } from '$api/analytics';
	import type { AnalyticsDashboard } from '$types';
	import Card from '$components/ui/Card.svelte';
	import Skeleton from '$components/ui/Skeleton.svelte';
	import PageLayout from '$components/layout/PageLayout.svelte';
	import { Target, BookOpen, HelpCircle, TrendingUp, TrendingDown, BarChart2, Activity } from 'lucide-svelte';

	let dashboard: AnalyticsDashboard | null = null;
	let loading = true;

	onMount(async () => {
		try {
			const res = await analyticsApi.getDashboard();
			dashboard = res.data ?? null;
		} finally {
			loading = false;
		}
	});

	const statCards = [
		{ key: 'total_topics_studied',      label: 'Topics Studied',  icon: Target,    accent: 'bg-sky-500'    },
		{ key: 'total_summaries_generated', label: 'Summaries',       icon: BookOpen,  accent: 'bg-purple-500' },
		{ key: 'total_quizzes_taken',       label: 'Quizzes Taken',   icon: HelpCircle,accent: 'bg-green-500'  },
		{ key: 'overall_quiz_accuracy',     label: 'Quiz Accuracy',   icon: TrendingUp,accent: 'bg-brand-500', suffix: '%' },
	];

	function val(key: string): number {
		if (!dashboard) return 0;
		return (dashboard.summary as unknown as Record<string, number>)[key] ?? 0;
	}
</script>

<svelte:head><title>Analytics — AI GyanGuru</title></svelte:head>

<PageLayout title="Analytics" subtitle="Track your learning progress and performance over time">

	<!-- ── 4 stat cards ─────────────────────────────────────────────────── -->
	<div class="grid grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
		{#each statCards as s}
			<Card padding="md">
				{#if loading}
					<Skeleton height="h-14" />
				{:else}
					<div class="flex items-start justify-between gap-3">
						<div>
							<p class="text-xs font-medium text-gray-500 dark:text-gray-400">{s.label}</p>
							<p class="mt-1.5 text-3xl font-bold text-gray-900 dark:text-white tabular-nums">
								{val(s.key)}{s.suffix ?? ''}
							</p>
						</div>
						<div class="h-9 w-9 rounded-xl {s.accent} flex items-center justify-center flex-shrink-0 shadow-sm">
							<svelte:component this={s.icon} class="h-4.5 w-4.5 text-white" />
						</div>
					</div>
				{/if}
			</Card>
		{/each}
	</div>

	<!-- ── 2-col: Daily Activity | Quiz Accuracy ────────────────────────── -->
	<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">

		<!-- Daily Activity -->
		<Card padding="md">
			<h3 class="card-title flex items-center gap-2 mb-5">
				<BarChart2 class="h-4 w-4 text-gray-400" />
				Daily Activity <span class="text-xs font-normal text-gray-400 ml-1">(last 30 days)</span>
			</h3>
			{#if loading}
				<Skeleton height="h-40" />
			{:else if dashboard?.daily_activity?.length}
				{@const maxV = Math.max(...dashboard.daily_activity.map(d => d.count), 1)}
				<div class="flex items-end gap-0.5 h-40">
					{#each dashboard.daily_activity as day}
						<div
							class="flex-1 rounded-t-sm bg-sky-400 dark:bg-sky-500 min-h-[3px]
							       transition-all hover:bg-sky-500 dark:hover:bg-sky-400 cursor-default"
							style="height: {Math.max((day.count / maxV) * 100, 3)}%"
							title="{day.date}: {day.count} activities"
						></div>
					{/each}
				</div>
			{:else}
				<div class="flex flex-col items-center justify-center h-40 text-center gap-3">
					<div class="h-12 w-12 rounded-2xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
						<BarChart2 class="h-6 w-6 text-gray-300 dark:text-gray-600" />
					</div>
					<div>
						<p class="text-sm font-medium text-gray-500 dark:text-gray-400">No activity data yet</p>
						<p class="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
							Complete some learning activities to see your daily chart.
						</p>
					</div>
				</div>
			{/if}
		</Card>

		<!-- Quiz Accuracy Trend -->
		<Card padding="md">
			<h3 class="card-title flex items-center gap-2 mb-5">
				<TrendingUp class="h-4 w-4 text-gray-400" />
				Quiz Accuracy Trend <span class="text-xs font-normal text-gray-400 ml-1">(last 30 days)</span>
			</h3>
			{#if loading}
				<Skeleton height="h-40" />
			{:else if dashboard?.quiz_accuracy_trend?.length}
				<div class="flex items-end gap-0.5 h-40">
					{#each dashboard.quiz_accuracy_trend as day}
						<div
							class="flex-1 rounded-t-sm bg-green-400 dark:bg-green-500 min-h-[3px]
							       transition-all hover:bg-green-500 dark:hover:bg-green-400 cursor-default"
							style="height: {Math.max(day.count, 3)}%"
							title="{day.date}: {day.count}%"
						></div>
					{/each}
				</div>
			{:else}
				<div class="flex flex-col items-center justify-center h-40 text-center gap-3">
					<div class="h-12 w-12 rounded-2xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
						<TrendingUp class="h-6 w-6 text-gray-300 dark:text-gray-600" />
					</div>
					<div>
						<p class="text-sm font-medium text-gray-500 dark:text-gray-400">No quiz data yet</p>
						<p class="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
							Complete some quizzes to see your accuracy trend.
						</p>
					</div>
				</div>
			{/if}
		</Card>
	</div>

	<!-- ── 2-col: Weak Areas | Strong Areas ─────────────────────────────── -->
	<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">

		<!-- Weak Areas -->
		<Card padding="md">
			<h3 class="card-title flex items-center gap-2 mb-5">
				<TrendingDown class="h-4 w-4 text-red-400" />
				Weak Areas
			</h3>
			{#if loading}
				<div class="space-y-3">
					{#each Array(4) as _}<Skeleton height="h-10" />{/each}
				</div>
			{:else if dashboard?.weak_areas?.length}
				<div class="space-y-4">
					{#each dashboard.weak_areas as area}
						<div>
							<div class="flex justify-between text-sm mb-1.5">
								<span class="font-medium text-gray-700 dark:text-gray-300">{area.category}</span>
								<span class="font-bold text-red-600 dark:text-red-400">{area.accuracy}%</span>
							</div>
							<div class="progress-bar">
								<div class="progress-fill bg-red-400" style="width:{area.accuracy}%"></div>
							</div>
						</div>
					{/each}
				</div>
			{:else}
				<div class="flex flex-col items-center justify-center py-10 text-center gap-3">
					<div class="h-12 w-12 rounded-2xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
						<TrendingDown class="h-6 w-6 text-gray-300 dark:text-gray-600" />
					</div>
					<div>
						<p class="text-sm font-medium text-gray-500 dark:text-gray-400">No weak areas found</p>
						<p class="text-xs text-gray-400 dark:text-gray-500 mt-0.5">Take some quizzes to identify areas for improvement.</p>
					</div>
				</div>
			{/if}
		</Card>

		<!-- Strong Areas -->
		<Card padding="md">
			<h3 class="card-title flex items-center gap-2 mb-5">
				<TrendingUp class="h-4 w-4 text-green-400" />
				Strong Areas
			</h3>
			{#if loading}
				<div class="space-y-3">
					{#each Array(4) as _}<Skeleton height="h-10" />{/each}
				</div>
			{:else if dashboard?.strong_areas?.length}
				<div class="space-y-4">
					{#each dashboard.strong_areas as area}
						<div>
							<div class="flex justify-between text-sm mb-1.5">
								<span class="font-medium text-gray-700 dark:text-gray-300">{area.category}</span>
								<span class="font-bold text-green-600 dark:text-green-400">{area.accuracy}%</span>
							</div>
							<div class="progress-bar">
								<div class="progress-fill bg-green-400" style="width:{area.accuracy}%"></div>
							</div>
						</div>
					{/each}
				</div>
			{:else}
				<div class="flex flex-col items-center justify-center py-10 text-center gap-3">
					<div class="h-12 w-12 rounded-2xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
						<TrendingUp class="h-6 w-6 text-gray-300 dark:text-gray-600" />
					</div>
					<div>
						<p class="text-sm font-medium text-gray-500 dark:text-gray-400">No strong areas yet</p>
						<p class="text-xs text-gray-400 dark:text-gray-500 mt-0.5">Keep taking quizzes to build your strengths.</p>
					</div>
				</div>
			{/if}
		</Card>
	</div>

	<!-- ── Activity Heatmap — full width ────────────────────────────────── -->
	<Card padding="md">
		<h3 class="card-title flex items-center gap-2 mb-5">
			<Activity class="h-4 w-4 text-gray-400" />
			Activity Heatmap <span class="text-xs font-normal text-gray-400 ml-1">(last 90 days)</span>
		</h3>
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
						class:bg-sky-200={intensity === 1}
						class:bg-sky-300={intensity === 2}
						class:bg-sky-400={intensity === 3}
						class:bg-sky-500={intensity === 4}
						class:bg-sky-600={intensity >= 5}
						title="{day.date}: {day.count} activities"
					></div>
				{/each}
			</div>
			<!-- Legend -->
			<div class="flex items-center gap-2 mt-4 text-xs text-gray-400">
				<span>Less</span>
				{#each [0,1,2,3,4,5] as i}
					<div class="h-3.5 w-3.5 rounded-sm
					            {i === 0 ? 'bg-gray-100 dark:bg-gray-800' :
					             i === 1 ? 'bg-sky-200' :
					             i === 2 ? 'bg-sky-300' :
					             i === 3 ? 'bg-sky-400' :
					             i === 4 ? 'bg-sky-500' : 'bg-sky-600'}"></div>
				{/each}
				<span>More</span>
			</div>
		{:else}
			<div class="flex flex-col items-center justify-center py-10 text-center gap-3">
				<div class="h-12 w-12 rounded-2xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
					<Activity class="h-6 w-6 text-gray-300 dark:text-gray-600" />
				</div>
				<div>
					<p class="text-sm font-medium text-gray-500 dark:text-gray-400">No activity data yet</p>
					<p class="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
						Start learning — your activity heatmap will appear here.
					</p>
				</div>
			</div>
		{/if}
	</Card>

</PageLayout>
