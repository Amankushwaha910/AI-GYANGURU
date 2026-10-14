<script lang="ts">
	import { goto } from '$app/navigation';
	import { isAuthenticated, authStore } from '$stores/auth';

	// Redirect once auth state is resolved. Keeping this in one place avoids
	// duplicate dashboard navigations when an authenticated user visits `/`.
	$: if ($authStore.initialized && !$authStore.loading) {
		if ($isAuthenticated) {
			goto('/dashboard');
		} else {
			goto('/login');
		}
	}
</script>

<!-- Blank while redirecting -->
<div class="flex h-screen items-center justify-center bg-gray-50 dark:bg-gray-950">
	<div class="h-8 w-8 animate-spin rounded-full border-4 border-brand-200 border-t-brand-600"></div>
</div>
