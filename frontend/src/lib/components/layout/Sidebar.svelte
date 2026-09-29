<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { authStore, currentUser } from '$stores/auth';
	import { themeStore } from '$stores/theme';
	import { toast } from '$stores/toast';
	import { authApi } from '$api/auth';
	import { cn } from '$lib/utils';
	import {
		LayoutDashboard, BookOpen, Lightbulb, HelpCircle,
		Upload, BarChart2, Clock, Sun, Moon, LogOut,
		GraduationCap, User
	} from 'lucide-svelte';

	const navItems = [
		{ href: '/dashboard',   label: 'Dashboard',   icon: LayoutDashboard },
		{ href: '/summary',     label: 'Summary',     icon: BookOpen },
		{ href: '/explanation', label: 'Explanation', icon: Lightbulb },
		{ href: '/quiz',        label: 'Quiz',        icon: HelpCircle },
		{ href: '/upload',      label: 'Upload',      icon: Upload },
		{ href: '/analytics',   label: 'Analytics',   icon: BarChart2 },
		{ href: '/history',     label: 'History',     icon: Clock },
	];

	$: currentPath = $page.url.pathname;

	async function handleLogout() {
		try { await authApi.logout(); } catch {}
		authStore.clearAuth();
		toast.success('Logged out successfully');
		goto('/login');
	}
</script>

<aside
	class="flex h-screen w-64 flex-col fixed left-0 top-0 z-30
	       border-r border-gray-200 dark:border-gray-800
	       bg-white dark:bg-gray-950"
>
	<!-- ── Logo ─────────────────────────────────────────────── -->
	<div class="flex items-center gap-3 px-5 h-16 border-b border-gray-100 dark:border-gray-800 flex-shrink-0">
		<div class="flex h-8 w-8 items-center justify-center rounded-lg bg-sky-500 shadow-sm flex-shrink-0">
			<GraduationCap class="h-4.5 w-4.5 text-white" />
		</div>
		<div class="min-w-0">
			<p class="text-sm font-bold text-gray-900 dark:text-white leading-tight">AI GyanGuru</p>
			<p class="text-[11px] text-gray-400 dark:text-gray-500 leading-tight">Learning Platform</p>
		</div>
	</div>

	<!-- ── Nav ──────────────────────────────────────────────── -->
	<nav class="flex-1 overflow-y-auto px-3 py-3 space-y-0.5">
		{#each navItems as item}
			<a
				href={item.href}
				class={cn(
					'flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-150',
					currentPath.startsWith(item.href)
						? 'bg-brand-50 text-brand-700 dark:bg-brand-950/60 dark:text-brand-300'
						: 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-gray-100'
				)}
			>
				<svelte:component
					this={item.icon}
					class={cn(
						'h-4 w-4 flex-shrink-0',
						currentPath.startsWith(item.href)
							? 'text-brand-600 dark:text-brand-400'
							: 'text-gray-400 dark:text-gray-500'
					)}
				/>
				{item.label}
			</a>
		{/each}
	</nav>

	<!-- ── Bottom ────────────────────────────────────────────── -->
	<div class="border-t border-gray-100 dark:border-gray-800 p-3 space-y-0.5 flex-shrink-0">
		<!-- Theme toggle -->
		<button
			on:click={() => themeStore.toggle()}
			class="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium
			       text-gray-600 dark:text-gray-400
			       hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
		>
			{#if $themeStore === 'dark'}
				<Sun class="h-4 w-4 text-gray-400 dark:text-gray-500" />
				Light Mode
			{:else}
				<Moon class="h-4 w-4 text-gray-400" />
				Dark Mode
			{/if}
		</button>

		<!-- Profile link -->
		<a
			href="/profile"
			class="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium
			       text-gray-600 dark:text-gray-400
			       hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
		>
			<User class="h-4 w-4 text-gray-400 dark:text-gray-500" />
			<span class="truncate">
				{$currentUser?.profile?.full_name || $currentUser?.email?.split('@')[0] || 'Profile'}
			</span>
		</a>

		<!-- Logout -->
		<button
			on:click={handleLogout}
			class="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium
			       text-red-500 dark:text-red-400
			       hover:bg-red-50 dark:hover:bg-red-950/40 transition-colors"
		>
			<LogOut class="h-4 w-4" />
			Log out
		</button>
	</div>
</aside>
