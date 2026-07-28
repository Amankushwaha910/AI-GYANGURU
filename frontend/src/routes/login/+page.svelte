<script lang="ts">
	import { goto } from '$app/navigation';
	import { authStore } from '$stores/auth';
	import { toast } from '$stores/toast';
	import { authApi } from '$api/auth';
	import { ApiClientError } from '$api/client';
	import Button from '$components/ui/Button.svelte';
	import Input from '$components/ui/Input.svelte';
	import { GraduationCap } from 'lucide-svelte';

	let email = '';
	let password = '';
	let loading = false;
	let errors = { email: '', password: '', form: '' };

	async function handleLogin() {
		errors = { email: '', password: '', form: '' };

		if (!email) { errors.email = 'Email is required'; return; }
		if (!password) { errors.password = 'Password is required'; return; }

		loading = true;
		try {
			const res = await authApi.login({ email, password });
			if (res.data) {
				authStore.setTokens(res.data.access_token, res.data.refresh_token);
				const meRes = await authApi.me();
				if (meRes.data) authStore.setUser(meRes.data);
				toast.success('Welcome back!');
				goto('/dashboard');
			}
		} catch (err) {
			if (err instanceof ApiClientError) {
				errors.form = err.message;
			} else {
				errors.form = 'Login failed. Please try again.';
			}
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head><title>Login — AI GyanGuru</title></svelte:head>

<div class="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-950 px-4">
	<div class="w-full max-w-md">
		<!-- Logo -->
		<div class="text-center mb-8">
			<div class="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-600 shadow-lg mb-4">
				<GraduationCap class="h-6 w-6 text-white" />
			</div>
			<h1 class="text-2xl font-bold text-gray-900 dark:text-white">Welcome back</h1>
			<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">Sign in to your AI GyanGuru account</p>
		</div>

		<!-- Form card -->
		<div class="rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-8 shadow-sm">
			<form on:submit|preventDefault={handleLogin} class="space-y-5">
				{#if errors.form}
					<div class="rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 px-4 py-3 text-sm text-red-700 dark:text-red-300">
						{errors.form}
					</div>
				{/if}

				<Input
					type="email"
					label="Email"
					placeholder="you@example.com"
					bind:value={email}
					error={errors.email}
					required
				/>

				<Input
					type="password"
					label="Password"
					placeholder="••••••••"
					bind:value={password}
					error={errors.password}
					required
				/>

				<Button type="submit" {loading} disabled={loading} class="w-full" size="lg">
					Sign In
				</Button>
			</form>
		</div>

		<p class="mt-6 text-center text-sm text-gray-500 dark:text-gray-400">
			Don't have an account?
			<a href="/register" class="font-medium text-brand-600 hover:text-brand-700 dark:text-brand-400">Create one free</a>
		</p>
	</div>
</div>
