<script lang="ts">
	import { goto } from '$app/navigation';
	import { authStore } from '$stores/auth';
	import { toast } from '$stores/toast';
	import { authApi } from '$api/auth';
	import { ApiClientError } from '$api/client';
	import Button from '$components/ui/Button.svelte';
	import Input from '$components/ui/Input.svelte';
	import { GraduationCap, Eye, EyeOff } from 'lucide-svelte';

	let email = '';
	let password = '';
	let showPassword = false;
	let loading = false;
	let errors = { email: '', password: '', form: '' };

	async function handleLogin() {
		errors = { email: '', password: '', form: '' };
		if (!email)    { errors.email    = 'Email is required';    return; }
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
			} else if (err instanceof TypeError) {
				errors.form = 'Cannot connect to the server. Please try again.';
			} else {
				errors.form = 'Login failed. Please try again.';
			}
		} finally {
			loading = false;
		}
	}

	/* Floating educational icons arranged in an orbit */
	const floatIcons = [
		{ emoji: '📚', top: '12%', left: '14%', delay: '0s',    dur: '3.8s' },
		{ emoji: '🎯', top: '8%',  left: '58%', delay: '0.7s',  dur: '4.2s' },
		{ emoji: '💡', top: '28%', left: '80%', delay: '1.3s',  dur: '3.6s' },
		{ emoji: '✏️', top: '60%', left: '84%', delay: '0.4s',  dur: '4.0s' },
		{ emoji: '🔬', top: '80%', left: '68%', delay: '1.0s',  dur: '3.7s' },
		{ emoji: '🏆', top: '84%', left: '22%', delay: '0.6s',  dur: '4.3s' },
		{ emoji: '📊', top: '68%', left: '8%',  delay: '1.5s',  dur: '3.5s' },
		{ emoji: '⚡', top: '36%', left: '4%',  delay: '0.2s',  dur: '4.1s' },
	];
</script>

<svelte:head><title>Sign In — AI GyanGuru</title></svelte:head>

<div class="flex min-h-screen">

	<!-- ═══════════════════ LEFT — 50 % ═══════════════════ -->
	<div class="hidden lg:flex w-1/2 relative overflow-hidden items-center justify-center"
	     style="background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 35%, #7dd3fc 65%, #38bdf8 100%);">

		<!-- Soft circle rings -->
		<div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
		            w-[460px] h-[460px] rounded-full border border-sky-300/50 pointer-events-none"></div>
		<div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
		            w-[320px] h-[320px] rounded-full border border-sky-400/40 pointer-events-none"></div>
		<div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
		            w-[200px] h-[200px] rounded-full border border-sky-500/30 pointer-events-none"></div>

		<!-- Soft blobs -->
		<div class="absolute -top-20 -left-20 w-72 h-72 rounded-full
		            bg-sky-200/50 blur-3xl pointer-events-none"></div>
		<div class="absolute -bottom-24 -right-16 w-80 h-80 rounded-full
		            bg-blue-200/40 blur-3xl pointer-events-none"></div>

		<!-- Floating educational icons -->
		{#each floatIcons as icon}
			<span
				class="absolute text-2xl select-none pointer-events-none"
				style="top:{icon.top}; left:{icon.left};
				       animation: floatIcon {icon.dur} ease-in-out {icon.delay} infinite;"
			>{icon.emoji}</span>
		{/each}

		<!-- Central branding -->
		<div class="relative z-10 flex flex-col items-center text-center px-10">
			<!-- Logo icon -->
			<div class="flex h-20 w-20 items-center justify-center rounded-2xl
			            bg-white/70 backdrop-blur-sm shadow-xl mb-6
			            ring-2 ring-sky-200/80">
				<GraduationCap class="h-11 w-11 text-sky-600" />
			</div>

			<!-- App name -->
			<h1 class="text-4xl font-bold text-sky-900 tracking-tight mb-2">
				AI GyanGuru
			</h1>

			<!-- Tagline -->
			<p class="text-sky-700 text-lg font-medium leading-relaxed">
				Learn Smarter.<br>Grow Faster.
			</p>
		</div>
	</div>

	<!-- ═══════════════════ RIGHT — 50 % ═══════════════════ -->
	<div class="flex w-full lg:w-1/2 flex-col items-center justify-center
	            bg-white dark:bg-gray-950 px-6 sm:px-12 py-12">
		<div class="w-full max-w-md">

			<!-- Mobile logo (visible only on small screens) -->
			<div class="flex justify-center mb-8 lg:hidden">
				<div class="flex items-center gap-3">
					<div class="flex h-9 w-9 items-center justify-center rounded-xl bg-sky-500">
						<GraduationCap class="h-5 w-5 text-white" />
					</div>
					<span class="text-lg font-bold text-gray-900 dark:text-white">AI GyanGuru</span>
				</div>
			</div>

			<!-- Heading -->
			<div class="mb-7">
				<h2 class="text-2xl font-bold text-gray-900 dark:text-white tracking-tight">
					Sign in to AI GyanGuru
				</h2>
				<p class="mt-1.5 text-sm text-gray-500 dark:text-gray-400">
					Enter your credentials to continue learning.
				</p>
			</div>

			<!-- Form -->
			<form on:submit|preventDefault={handleLogin} class="space-y-4">

				{#if errors.form}
					<div class="rounded-xl border border-red-200 dark:border-red-800
					            bg-red-50 dark:bg-red-900/20
					            px-4 py-3 text-sm text-red-700 dark:text-red-300">
						{errors.form}
					</div>
				{/if}

				<Input
					type="email"
					label="Email address"
					placeholder="you@example.com"
					bind:value={email}
					error={errors.email}
					required
				/>

				<!-- Password with visibility toggle -->
				<div class="flex flex-col gap-1.5">
					<label for="pw-login"
					       class="text-sm font-medium text-gray-700 dark:text-gray-300">
						Password
					</label>
					<div class="relative">
						{#if showPassword}
							<input
								id="pw-login"
								type="text"
								placeholder="••••••••"
								bind:value={password}
								required
								class="h-10 w-full rounded-xl border px-4 pr-11 text-sm
								       bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100
								       placeholder-gray-400 dark:placeholder-gray-500
								       focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent
								       {errors.password ? 'border-red-400' : 'border-gray-300 dark:border-gray-700'}"
							/>
						{:else}
							<input
								id="pw-login"
								type="password"
								placeholder="••••••••"
								bind:value={password}
								required
								class="h-10 w-full rounded-xl border px-4 pr-11 text-sm
								       bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100
								       placeholder-gray-400 dark:placeholder-gray-500
								       focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent
								       {errors.password ? 'border-red-400' : 'border-gray-300 dark:border-gray-700'}"
							/>
						{/if}
						<button
							type="button"
							on:click={() => (showPassword = !showPassword)}
							class="absolute right-3 top-1/2 -translate-y-1/2
							       text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
							aria-label={showPassword ? 'Hide password' : 'Show password'}
						>
							{#if showPassword}
								<EyeOff class="h-4 w-4" />
							{:else}
								<Eye class="h-4 w-4" />
							{/if}
						</button>
					</div>
					{#if errors.password}
						<p class="text-xs text-red-600 dark:text-red-400">{errors.password}</p>
					{/if}
				</div>

				<!-- Remember + Forgot -->
				<div class="flex items-center justify-between text-sm">
					<label class="flex items-center gap-2 cursor-pointer select-none">
						<input
							type="checkbox"
							class="h-4 w-4 rounded border-gray-300 dark:border-gray-600
							       text-sky-600 focus:ring-sky-500"
						/>
						<span class="text-gray-600 dark:text-gray-400">Keep me signed in</span>
					</label>
					<a href="/forgot-password"
					   class="font-medium text-sky-600 dark:text-sky-400 hover:underline">
						Forgot password?
					</a>
				</div>

				<button
					type="submit"
					disabled={loading}
					class="w-full h-12 rounded-xl text-base font-semibold text-white transition-all
					       bg-sky-500 hover:bg-sky-600 active:scale-[0.98]
					       disabled:opacity-60 disabled:pointer-events-none
					       flex items-center justify-center gap-2 shadow-sm"
				>
					{#if loading}
						<svg class="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
							<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
						</svg>
						Signing in…
					{:else}
						Sign In
					{/if}
				</button>
			</form>

			<p class="mt-7 text-center text-sm text-gray-500 dark:text-gray-400">
				Don't have an account?
				<a href="/register"
				   class="font-semibold text-sky-600 dark:text-sky-400 hover:underline">
					Create one free
				</a>
			</p>
		</div>
	</div>
</div>

<style>
	@keyframes floatIcon {
		0%, 100% { transform: translateY(0)   rotate(0deg);  }
		33%       { transform: translateY(-9px) rotate(4deg);  }
		66%       { transform: translateY(5px)  rotate(-3deg); }
	}
</style>
