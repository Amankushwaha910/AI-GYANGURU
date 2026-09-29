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
		if (p.length < 8)      return 'Minimum 8 characters';
		if (!/[A-Z]/.test(p))  return 'Must include an uppercase letter';
		if (!/[a-z]/.test(p))  return 'Must include a lowercase letter';
		if (!/\d/.test(p))     return 'Must include a number';
		return '';
	}

	async function handleRegister() {
		errors = { fullName: '', email: '', password: '', form: '' };
		const pwErr = validatePassword(password);
		if (pwErr)  { errors.password = pwErr;               return; }
		if (!email) { errors.email    = 'Email is required'; return; }

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

	$: strength = (() => {
		let s = 0;
		if (password.length >= 8) s++;
		if (/[A-Z]/.test(password)) s++;
		if (/[a-z]/.test(password)) s++;
		if (/\d/.test(password)) s++;
		return s;
	})();
	const strengthColors = ['', 'bg-red-400', 'bg-amber-400', 'bg-blue-400', 'bg-green-500'];
	const strengthLabels = ['', 'Weak', 'Fair', 'Good', 'Strong'];

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

<svelte:head><title>Create Account — AI GyanGuru</title></svelte:head>

<div class="flex min-h-screen">

	<!-- ═══════════════════ LEFT — 50 % (identical to Login) ═══════════════════ -->
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
			<div class="flex h-20 w-20 items-center justify-center rounded-2xl
			            bg-white/70 backdrop-blur-sm shadow-xl mb-6
			            ring-2 ring-sky-200/80">
				<GraduationCap class="h-11 w-11 text-sky-600" />
			</div>
			<h1 class="text-4xl font-bold text-sky-900 tracking-tight mb-2">AI GyanGuru</h1>
			<p class="text-sky-700 text-lg font-medium leading-relaxed">
				Learn Smarter.<br>Grow Faster.
			</p>
		</div>
	</div>

	<!-- ═══════════════════ RIGHT — 50 % ═══════════════════ -->
	<div class="flex w-full lg:w-1/2 flex-col items-center justify-center
	            bg-white dark:bg-gray-950 px-6 sm:px-12 py-12">
		<div class="w-full max-w-md">

			<!-- Mobile logo -->
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
					Create your account
				</h2>
				<p class="mt-1.5 text-sm text-gray-500 dark:text-gray-400">
					Start learning smarter with AI.
				</p>
			</div>

			<!-- Form -->
			<form on:submit|preventDefault={handleRegister} class="space-y-4">

				{#if errors.form}
					<div class="rounded-xl border border-red-200 dark:border-red-800
					            bg-red-50 dark:bg-red-900/20
					            px-4 py-3 text-sm text-red-700 dark:text-red-300">
						{errors.form}
					</div>
				{/if}

				<Input
					label="Full Name"
					placeholder="Aman Sharma"
					bind:value={fullName}
					error={errors.fullName}
				/>

				<Input
					type="email"
					label="Email address"
					placeholder="you@example.com"
					bind:value={email}
					error={errors.email}
					required
				/>

				<!-- Password + strength -->
				<div>
					<Input
						type="password"
						label="Password"
						placeholder="••••••••"
						bind:value={password}
						error={errors.password}
						required
					/>
					{#if password}
						<div class="mt-2 space-y-1">
							<div class="flex gap-1">
								{#each Array(4) as _, i}
									<div class="h-1 flex-1 rounded-full transition-all duration-300
									            {i < strength ? strengthColors[strength] : 'bg-gray-200 dark:bg-gray-700'}">
									</div>
								{/each}
							</div>
							<p class="text-xs text-gray-400">{strengthLabels[strength]}</p>
						</div>
					{/if}
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
						Creating account…
					{:else}
						Create Account
					{/if}
				</button>
			</form>

			<p class="mt-7 text-center text-sm text-gray-500 dark:text-gray-400">
				Already have an account?
				<a href="/login"
				   class="font-semibold text-sky-600 dark:text-sky-400 hover:underline">
					Sign in
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
