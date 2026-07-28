<script lang="ts">
	import { onMount } from 'svelte';
	import { currentUser } from '$stores/auth';
	import { analyticsApi } from '$api/analytics';
	import { formatRelativeTime, HISTORY_TYPE_COLORS, HISTORY_TYPE_LABELS } from '$lib/utils';
	import type { DashboardData } from '$types';
	import Card from '$components/ui/Card.svelte';
	import Skeleton from '$components/ui/Skeleton.svelte';
	import Button from '$components/ui/Button.svelte';
	import PageLayout from '$components/layout/PageLayout.svelte';
	import { BookOpen, Lightbulb, HelpCircle, Upload, TrendingUp, Target, Zap, Clock } from 'lucide-svelte';
	import { onDestroy } from 'svelte';

	let dashboard: DashboardData | null = null;
	let loading = true;
	let error = '';

	onMount(async () => {
		try {
			const res = await analyticsApi.getHomeDashboard();
			dashboard = res.data ?? null;
		} catch (e: any) {
			error = e.message;
		} finally {
			loading = false;
		}
	});

	$: greeting = (() => {
		const h = new Date().getHours();
		if (h < 12) return 'Good morning';
		if (h < 17) return 'Good afternoon';
		return 'Good evening';
	})();

	$: displayName = $currentUser?.profile?.full_name || $currentUser?.email?.split('@')[0] || 'Learner';

	const quickActions = [
		{ href: '/summary', label: 'Generate Summary', icon: BookOpen, color: 'bg-blue-500' },
		{ href: '/explanation', label: 'Get Explanation', icon: Lightbulb, color: 'bg-purple-500' },
		{ href: '/quiz', label: 'Start Quiz', icon: HelpCircle, color: 'bg-green-500' },
		{ href: '/upload', label: 'Upload File', icon: Upload, color: 'bg-orange-500' }
	];

	const statCards = [
		{ key: 'total_topics_studied' as const, label: 'Topics Studied', icon: Target, color: 'text-blue-500' },
		{ key: 'total_summaries_generated' as const, label: 'Summaries', icon: BookOpen, color: 'text-purple-500' },
		{ key: 'total_quizzes_taken' as const, label: 'Quizzes Taken', icon: HelpCircle, color: 'text-green-500' },
		{ key: 'overall_quiz_accuracy' as const, label: 'Quiz Accuracy', icon: TrendingUp, color: 'text-brand-500', suffix: '%' }
	];

	function getStatValue(key: string): number {
		if (!dashboard) return 0;
		const s = dashboard.summary as unknown as Record<string, number>;
		return s[key] ?? 0;
	}
</script>

<svelte:head><title>Dashboard — AI GyanGuru</title></svelte:head>

<PageLayout>
	<!-- Greeting banner -->
	<div class="mb-8 rounded-2xl bg-gradient-to-r from-brand-600 to-purple-600 p-6 text-white shadow-lg">
		<div class="flex items-center justify-between">
			<div>
				<p class="text-brand-200 text-sm font-medium">{greeting},</p>
				<h2 class="text-2xl font-bold mt-0.5">{displayName} 👋</h2>
				<p class="mt-1 text-sm text-brand-200">Ready to learn something new today?</p>
			</div>
			<div class="hidden md:flex h-16 w-16 items-center justify-center rounded-2xl bg-white/10">
				<Zap class="h-8 w-8 text-white" />
			</div>
		</div>
	</div>

	<!-- Stats row -->
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
						<div class="rounded-lg bg-gray-50 dark:bg-gray-800 p-2">
							<svelte:component this={stat.icon} class="h-5 w-5 {stat.color}" />
						</div>
					</div>
				{/if}
			</Card>
		{/each}
	</div>

	<!-- Quick Actions -->
	<div class="mb-8">
		<h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4">Quick Actions</h3>
		<div class="grid grid-cols-2 md:grid-cols-4 gap-4">
			{#each quickActions as action}
				<a href={action.href} class="group flex flex-col items-center gap-3 rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-5 hover:shadow-md hover:-translate-y-0.5 transition-all duration-200">
					<div class="h-12 w-12 rounded-xl {action.color} flex items-center justify-center shadow-sm group-hover:scale-110 transition-transform">
						<svelte:component this={action.icon} class="h-6 w-6 text-white" />
					</div>
					<span class="text-sm font-medium text-gray-700 dark:text-gray-300 text-center">{action.label}</span>
				</a>
			{/each}
		</div>
	</div>

	<!-- Recent Activity -->
	<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
		<Card padding="md">
			<div class="flex items-center justify-between mb-5">
				<div class="flex items-center gap-2">
					<Clock class="h-4 w-4 text-gray-400" />
					<h3 class="text-sm font-semibold text-gray-900 dark:text-white">Recent Activity</h3>
				</div>
				<a href="/history" class="text-xs text-brand-600 dark:text-brand-400 hover:underline font-medium">View all</a>
			</div>

			{#if loading}
				<div class="space-y-3">
					{#each Array(5) as _}
						<div class="flex gap-3">
							<Skeleton height="h-8" width="w-8" rounded="rounded-lg" />
							<div class="flex-1 space-y-1.5">
								<Skeleton height="h-3" width="w-3/4" />
								<Skeleton height="h-3" width="w-1/3" />
							</div>
						</div>
					{/each}
				</div>
			{:else if !dashboard?.recent_activity?.length}
				<p class="text-sm text-gray-400 dark:text-gray-500 py-4 text-center">No activity yet. Start learning!</p>
			{:else}
				<div class="space-y-3">
					{#each dashboard.recent_activity as item}
						<div class="flex items-start gap-3 p-2 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
							<span class="inline-flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg text-xs font-bold {HISTORY_TYPE_COLORS[item.item_type]}">
								{item.item_type[0].toUpperCase()}
							</span>
							<div class="flex-1 min-w-0">
								<p class="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">{item.topic}</p>
								<p class="text-xs text-gray-400 dark:text-gray-500">{HISTORY_TYPE_LABELS[item.item_type]} · {formatRelativeTime(item.created_at)}</p>
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</Card>

		<!-- Weekly chart -->
		<Card padding="md">
			<div class="flex items-center gap-2 mb-5">
				<TrendingUp class="h-4 w-4 text-gray-400" />
				<h3 class="text-sm font-semibold text-gray-900 dark:text-white">Weekly Activity</h3>
			</div>
			{#if loading}
				<Skeleton height="h-32" />
			{:else if dashboard?.weekly_activity?.length}
				<div class="flex items-end gap-1.5 h-32">
					{#each dashboard.weekly_activity.slice(-7) as day}
						{@const max = Math.max(...dashboard.weekly_activity.slice(-7).map(d => d.count), 1)}
						<div class="flex-1 flex flex-col items-center gap-1">
							<div
								class="w-full rounded-t-md bg-brand-500 dark:bg-brand-400 transition-all"
								style="height: {Math.max((day.count / max) * 100, 4)}%"
							></div>
							<span class="text-xs text-gray-400 truncate">{new Date(day.date).toLocaleDateString('en', { weekday: 'short' })}</span>
						</div>
					{/each}
				</div>
			{:else}
				<p class="text-sm text-gray-400 text-center py-10">No activity this week yet.</p>
			{/if}
		</Card>
	</div>
</PageLayout>
