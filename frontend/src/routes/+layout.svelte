<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { authStore, isAuthenticated } from '$stores/auth';
	import { themeStore } from '$stores/theme';
	import { toast } from '$stores/toast';
	import { authApi } from '$api/auth';
	import Toast from '$components/ui/Toast.svelte';
	import Sidebar from '$components/layout/Sidebar.svelte';

	// Public routes that don't require authentication
	const publicRoutes = ['/login', '/register', '/'];
	$: isPublic = publicRoutes.includes($page.url.pathname);

	onMount(async () => {
		themeStore.init();
		authStore.init();

		const token = browser ? localStorage.getItem('access_token') : null;

		if (token) {
			try {
				const res = await authApi.me();
				if (res.data) {
					authStore.setUser(res.data);
				} else {
					authStore.clearAuth();
				}
			} catch {
				authStore.clearAuth();
			}
		} else {
			authStore.setLoading(false);
		}
	});

	// Redirect unauthenticated users away from protected routes
	$: if (browser && !$isAuthenticated && !isPublic && $authStore.initialized && !$authStore.loading) {
		goto('/login');
	}
</script>

{#if isPublic}
	<slot />
{:else if $authStore.loading}
	<!-- Loading splash while verifying session -->
	<div class="flex h-screen items-center justify-center bg-gray-50 dark:bg-gray-950">
		<div class="flex flex-col items-center gap-4">
			<div class="h-10 w-10 animate-spin rounded-full border-4 border-brand-200 border-t-brand-600"></div>
			<p class="text-sm text-gray-500 dark:text-gray-400">Loading AI GyanGuru...</p>
		</div>
	</div>
{:else if $isAuthenticated}
	<div class="flex">
		<Sidebar />
		<div class="content-area">
			<slot />
		</div>
	</div>
{/if}

<Toast />
