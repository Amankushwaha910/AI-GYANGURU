<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { authStore, isAuthenticated } from '$stores/auth';
	import { themeStore } from '$stores/theme';
	import { authApi } from '$api/auth';
	import Toast from '$components/ui/Toast.svelte';
	import Sidebar from '$components/layout/Sidebar.svelte';

	// Public routes that don't require authentication
	const publicRoutes = ['/login', '/register', '/'];
	// During dev-server HMR, SvelteKit can briefly recreate the root layout
	// before the page store has its URL. Fall back to the browser's current path
	// for that transient state so auth gating does not crash the entire layout.
	$: routePath = $page?.url?.pathname ?? (browser ? window.location.pathname : '/');
	$: isPublic = publicRoutes.includes(routePath);

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
				// Token invalid/expired — clear session silently
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

{#if !isPublic && $authStore.loading}
	<!-- Loading splash while verifying session -->
	<div class="flex h-screen items-center justify-center bg-gray-50 dark:bg-gray-950">
		<div class="flex flex-col items-center gap-4">
			<div class="h-10 w-10 animate-spin rounded-full border-4 border-brand-200 border-t-brand-600"></div>
			<p class="text-sm text-gray-500 dark:text-gray-400">Loading AI GyanGuru...</p>
		</div>
	</div>
{:else if !isPublic && !$isAuthenticated}
	<!-- Keep protected page content hidden until authentication is resolved. -->
	<div class="h-screen bg-gray-50 dark:bg-gray-950"></div>
{:else}
	<!-- Keep one slot instance across public → authenticated SPA navigation. -->
	<div class:flex={!isPublic && $isAuthenticated}>
		{#if !isPublic && $isAuthenticated}
			<Sidebar />
		{/if}
		<div class:content-area={!isPublic && $isAuthenticated}>
			<slot />
		</div>
	</div>
{/if}

<Toast />
