<script lang="ts">
	import { onMount } from 'svelte';
	import { currentUser } from '$stores/auth';
	import { analyticsApi } from '$api/analytics';
	import { formatRelativeTime, HISTORY_TYPE_COLORS, HISTORY_TYPE_LABELS } from '$lib/utils';
	import type { DashboardData } from '$types';
	import Card from '$components/ui/Card.svelte';
	import Skeleton from '$components/ui/Skeleton.svelte';
	import PageLayout from '$components/layout/PageLayout.svelte';
	import {
		BookOpen, Lightbulb, HelpCircle, Upload,
		TrendingUp, Target, Zap, Clock, BarChart2
	} from 'lucide-svelte';

	let dashboard: DashboardData | null = null;
	let loading = true;

	onMount(async () => {
		try {
			const res = await analyticsApi.getHomeDashboard();
			dashboard = res.data ?? null;
		} catch {
			// non-fatal
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

	$: displayName =
		$currentUser?.profile?.full_name ||
		$currentUser?.email?.split('@')[0] ||
		'Learner';

	const quickActions = [
		{ href: '/summary',     label: 'Generate Summary',   icon: BookOpen,   accent: 'bg-blue-500',   light: 'bg-blue-50 dark:bg-blue-900/20',   text: 'text-blue-700 dark:text-blue-300'   },
		{ href: '/explanation', label: 'Get Explanation',    icon: Lightbulb,  accent: 'bg-purple-500', light: 'bg-purple-50 dark:bg-purple-900/20',text: 'text-purple-700 dark:text-purple-300'},
		{ href: '/quiz',        label: 'Start a Quiz',       icon: HelpCircle, accent: 'bg-green-500',  light: 'bg-green-50 dark:bg-green-900/20',  text: 'text-green-700 dark:text-green-300' },
		{ href: '/upload',      label: 'Upload File',        icon: Upload,     accent: 'bg-orange-500', light: 'bg-orange-50 dark:bg-orange-900/20',text: 'text-orange-700 dark:text-orange-300'},
	];

	const statCards = [
		{ key: 'total_topics_studied',      label: 'Topics Studied',  icon: Target,    accent: 'bg-sky-500'    },
		{ key: 'total_summaries_generated', label: 'Summaries',       icon: BookOpen,  accent: 'bg-purple-500' },
		{ key: 'total_quizzes_taken',       label: 'Quizzes Taken',   icon: HelpCircle,accent: 'bg-green-500'  },
		{ key: 'overall_quiz_accuracy',     label: 'Quiz Accuracy',   icon: TrendingUp,accent: 'bg-brand-500', suffix: '%' },
	];

	function val(key: string) {
		if (!dashboard) return 0;
		return (dashboard.summary as unknown as Record<string, number>)[key] ?? 0;
	}
</script>

<svelte:head><title>Dashboard — AI GyanGuru</title></svelte:head>

<PageLayout>

	<!-- ── Greeting banner ─────────────────────────────────────────────── -->
	<div class="mb-6 rounded-2xl bg-gradient-to-r from-sky-500 to-blue-600 px-7 py-5 shadow-sm">
		<div class="flex items-center justify-between gap-4">
			<div>
				<p class="text-sky-100 text-sm font-medium">{greeting},</p>
				<h2 class="text-xl font-bold text-white mt-0.5">{displayName} 👋</h2>
				<p class="mt-1 text-sm text-sky-100">Ready to learn something new today?</p>
			</div>
			<div class="hidden sm:flex h-12 w-12 items-center justify-center
			            rounded-xl bg-white/15 flex-shrink-0">
				<Zap class="h-6 w-6 text-white" />
			</div>
		</div>
	</div>

	<!-- ── Stat cards — 4 across ───────────────────────────────────────── -->
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

	<!-- ── Quick actions — 4 across ───────────────────────────────────── -->
	<div class="mb-6">
		<p class="section-title mb-3">Quick Actions</p>
		<div class="grid grid-cols-2 xl:grid-cols-4 gap-4">
			{#each quickActions as a}
				<a
					href={a.href}
					class="group flex items-center gap-4 rounded-2xl border border-gray-200
					       dark:border-gray-800 bg-white dark:bg-gray-900 px-5 py-4
					       hover:shadow-md hover:-translate-y-0.5 transition-all duration-200"
				>
					<div class="h-11 w-11 rounded-xl {a.accent} flex items-center justify-center
					            flex-shrink-0 shadow-sm group-hover:scale-105 transition-transform">
						<svelte:component this={a.icon} class="h-5 w-5 text-white" />
					</div>
					<span class="text-sm font-semibold text-gray-800 dark:text-gray-200">
						{a.label}
					</span>
				</a>
			{/each}
		</div>
	</div>

	<!-- ── Recent activity (left) + Weekly chart (right) ──────────────── -->
	<div class="grid grid-cols-1 lg:grid-cols-5 gap-6">

		<!-- Recent Activity — spans 3/5 -->
		<Card padding="md" class="lg:col-span-3">
			<div class="flex items-center justify-between mb-5">
				<div class="flex items-center gap-2">
					<Clock class="h-4 w-4 text-gray-400" />
					<h3 class="card-title">Recent Activity</h3>
				</div>
				<a href="/history"
				   class="text-xs text-sky-600 dark:text-sky-400 hover:underline font-medium">
					View all →
				</a>
			</div>

			{#if loading}
				<div class="space-y-3">
					{#each Array(6) as _}
						<div class="flex gap-3 items-center">
							<Skeleton height="h-9" width="w-9" rounded="rounded-xl" />
							<div class="flex-1 space-y-1.5">
								<Skeleton height="h-3" width="w-3/4" />
								<Skeleton height="h-3" width="w-1/3" />
							</div>
						</div>
					{/each}
				</div>
			{:else if !dashboard?.recent_activity?.length}
				<div class="flex flex-col items-center justify-center py-10 text-center">
					<Clock class="h-10 w-10 text-gray-200 dark:text-gray-700 mb-3" />
					<p class="text-sm font-medium text-gray-500 dark:text-gray-400">No activity yet</p>
					<p class="text-xs text-gray-400 dark:text-gray-600 mt-1">
						Start learning and your history will appear here.
					</p>
				</div>
			{:else}
				<div class="space-y-1">
					{#each dashboard.recent_activity as item}
						<div class="flex items-center gap-3 px-2 py-2.5 rounded-xl
						            hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
							<span class="inline-flex h-9 w-9 flex-shrink-0 items-center justify-center
							             rounded-xl text-xs font-bold {HISTORY_TYPE_COLORS[item.item_type]}">
								{item.item_type[0].toUpperCase()}
							</span>
							<div class="flex-1 min-w-0">
								<p class="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">
									{item.topic}
								</p>
								<p class="text-xs text-gray-400 dark:text-gray-500">
									{HISTORY_TYPE_LABELS[item.item_type]} · {formatRelativeTime(item.created_at)}
								</p>
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</Card>

		<!-- Weekly chart — spans 2/5 -->
		<Card padding="md" class="lg:col-span-2">
			<div class="flex items-center gap-2 mb-5">
				<BarChart2 class="h-4 w-4 text-gray-400" />
				<h3 class="card-title">This Week</h3>
			</div>
			{#if loading}
				<Skeleton height="h-40" />
			{:else if dashboard?.weekly_activity?.length}
				{@const slice = dashboard.weekly_activity.slice(-7)}
				{@const maxV = Math.max(...slice.map(d => d.count), 1)}
				<div class="flex items-end gap-2 h-40">
					{#each slice as day}
						<div class="flex-1 flex flex-col items-center gap-2">
							<div
								class="w-full rounded-t-lg bg-sky-400 dark:bg-sky-500 transition-all
								       hover:bg-sky-500 dark:hover:bg-sky-400 cursor-default"
								style="height: {Math.max((day.count / maxV) * 100, 6)}%"
								title="{day.date}: {day.count}"
							></div>
							<span class="text-[10px] text-gray-400 truncate w-full text-center">
								{new Date(day.date).toLocaleDateString('en', { weekday: 'short' })}
							</span>
						</div>
					{/each}
				</div>
			{:else}
				<div class="flex flex-col items-center justify-center h-40 text-center">
					<BarChart2 class="h-10 w-10 text-gray-200 dark:text-gray-700 mb-3" />
					<p class="text-sm text-gray-400 dark:text-gray-500">No activity this week</p>
				</div>
			{/if}
		</Card>
	</div>

</PageLayout>
