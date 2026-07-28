<script lang="ts">
	import { goto } from '$app/navigation';
	import { authStore } from '$stores/auth';
	import { toast } from '$stores/toast';
	import { authApi } from '$api/auth';
	import { ApiClientError } from '$api/client';
	import Button from '$components/ui/Button.svelte';
	import Input from '$components/ui/Input.svelte';
	import { GraduationCap } from 'lucide-svelte';

	let fullName = '';
	let email = '';
	let password = '';
	let loading = false;
	let errors = { fullName: '', email: '', password: '', form: '' };

	function validatePassword(p: string) {
		if (p.length < 8) return 'Minimum 8 characters';
		if (!/[A-Z]/.test(p)) return 'Must include an uppercase letter';
		if (!/[a-z]/.test(p)) return 'Must include a lowercase letter';
		if (!/\d/.test(p)) return 'Must include a number';
		return '';
	}

	async function handleRegister() {
		errors = { fullName: '', email: '', password: '', form: '' };
		const pwErr = validatePassword(password);
		if (pwErr) { errors.password = pwErr; return; }
		if (!email) { errors.email = 'Email is required'; return; }

		loading = true;
		try {
			const res = await authApi.register({ email, password, full_name: fullName });
			if (res.data) {
				authStore.setTokens(res.data.access_token, res.data.refresh_token);
				const meRes = await authApi.me();
				if (meRes.data) authStore.setUser(meRes.data);
				toast.success('Account created! Welcome to AI GyanGuru.');
				goto('/dashboard');
			}
		} catch (err) {
			if (err instanceof ApiClientError) {
				errors.form = err.message;
			} else {
				errors.form = 'Registration failed. Please try again.';
			}
		} finally {
			loading = false;
		}
	}

	// Live password strength
	$: strength = (() => {
		let score = 0;
		if (password.length >= 8) score++;
		if (/[A-Z]/.test(password)) score++;
		if (/[a-z]/.test(password)) score++;
		if (/\d/.test(password)) score++;
		return score;
	})();
</script>

<svelte:head><title>Register — AI GyanGuru</title></svelte:head>

<div class="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-950 px-4 py-10">
	<div class="w-full max-w-md">
		<div class="text-center mb-8">
			<div class="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-600 shadow-lg mb-4">
				<GraduationCap class="h-6 w-6 text-white" />
			</div>
			<h1 class="text-2xl font-bold text-gray-900 dark:text-white">Create your account</h1>
			<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">Start learning smarter with AI</p>
		</div>

		<div class="rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-8 shadow-sm">
			<form on:submit|preventDefault={handleRegister} class="space-y-5">
				{#if errors.form}
					<div class="rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 px-4 py-3 text-sm text-red-700 dark:text-red-300">
						{errors.form}
					</div>
				{/if}

				<Input label="Full Name" placeholder="Aman Sharma" bind:value={fullName} error={errors.fullName} />

				<Input type="email" label="Email" placeholder="you@example.com" bind:value={email} error={errors.email} required />

				<div>
					<Input type="password" label="Password" placeholder="••••••••" bind:value={password} error={errors.password} required />
					{#if password}
						<div class="mt-2 flex gap-1">
							{#each Array(4) as _, i}
								<div class="h-1 flex-1 rounded-full transition-colors {i < strength
									? strength <= 1 ? 'bg-red-400' : strength <= 2 ? 'bg-yellow-400' : strength <= 3 ? 'bg-blue-400' : 'bg-green-400'
									: 'bg-gray-200 dark:bg-gray-700'}"></div>
							{/each}
						</div>
						<p class="mt-1 text-xs text-gray-400">{['', 'Weak', 'Fair', 'Good', 'Strong'][strength]}</p>
					{/if}
				</div>

				<Button type="submit" {loading} disabled={loading} class="w-full" size="lg">
					Create Account
				</Button>
			</form>
		</div>

		<p class="mt-6 text-center text-sm text-gray-500 dark:text-gray-400">
			Already have an account?
			<a href="/login" class="font-medium text-brand-600 hover:text-brand-700 dark:text-brand-400">Sign in</a>
		</p>
	</div>
</div>
