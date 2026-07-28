<script lang="ts">
	import { goto } from '$app/navigation';
	import { authStore, currentUser } from '$stores/auth';
	import { toast } from '$stores/toast';
	import { authApi } from '$api/auth';
	import { api } from '$api/client';
	import { ApiClientError } from '$api/client';
	import type { APIResponse, User } from '$types';
	import Button from '$components/ui/Button.svelte';
	import Input from '$components/ui/Input.svelte';
	import Card from '$components/ui/Card.svelte';
	import PageLayout from '$components/layout/PageLayout.svelte';
	import { User as UserIcon, Lock, Trash2, Save } from 'lucide-svelte';

	let fullName = $currentUser?.profile?.full_name ?? '';
	let bio = $currentUser?.profile?.bio ?? '';
	let educationLevel = $currentUser?.profile?.education_level ?? '';
	let examTarget = $currentUser?.profile?.exam_target ?? '';

	let currentPassword = '';
	let newPassword = '';
	let confirmPassword = '';

	let savingProfile = false;
	let changingPassword = false;
	let showDeleteConfirm = false;

	async function saveProfile() {
		savingProfile = true;
		try {
			const res = await api.put<APIResponse<User>>('/users/me', {
				full_name: fullName, bio, education_level: educationLevel, exam_target: examTarget
			});
			if (res.data) authStore.setUser(res.data);
			toast.success('Profile updated');
		} catch (e: any) {
			toast.error(e instanceof ApiClientError ? e.message : 'Failed to update profile');
		} finally { savingProfile = false; }
	}

	async function changePassword() {
		if (newPassword !== confirmPassword) { toast.error('Passwords do not match'); return; }
		if (newPassword.length < 8) { toast.error('Password must be at least 8 characters'); return; }
		changingPassword = true;
		try {
			await authApi.changePassword({ current_password: currentPassword, new_password: newPassword });
			toast.success('Password changed successfully');
			currentPassword = ''; newPassword = ''; confirmPassword = '';
		} catch (e: any) {
			toast.error(e instanceof ApiClientError ? e.message : 'Failed to change password');
		} finally { changingPassword = false; }
	}

	async function deleteAccount() {
		try {
			await api.delete('/users/me');
			authStore.clearAuth();
			toast.info('Account deleted. Goodbye!');
			goto('/');
		} catch (e: any) {
			toast.error('Failed to delete account');
		}
	}
</script>

<svelte:head><title>Profile — AI GyanGuru</title></svelte:head>

<PageLayout title="Profile" subtitle="Manage your account and preferences">
	<div class="max-w-2xl space-y-6">
		<!-- Profile info -->
		<Card padding="lg">
			<div class="flex items-center gap-3 mb-6">
				<div class="h-9 w-9 rounded-xl bg-brand-100 dark:bg-brand-900/30 flex items-center justify-center">
					<UserIcon class="h-5 w-5 text-brand-600 dark:text-brand-400" />
				</div>
				<div>
					<h2 class="font-semibold text-gray-900 dark:text-white">Personal Information</h2>
					<p class="text-sm text-gray-500 dark:text-gray-400">Update your profile details</p>
				</div>
			</div>

			<div class="mb-4 p-3 rounded-xl bg-gray-50 dark:bg-gray-800">
				<p class="text-xs text-gray-500 dark:text-gray-400">Email</p>
				<p class="text-sm font-medium text-gray-800 dark:text-gray-200">{$currentUser?.email}</p>
			</div>

			<form on:submit|preventDefault={saveProfile} class="space-y-4">
				<Input label="Full Name" bind:value={fullName} placeholder="Your full name" />
				<div>
					<label for="bio" class="text-sm font-medium text-gray-700 dark:text-gray-300 block mb-1.5">Bio</label>
					<textarea
						id="bio"
						bind:value={bio}
						placeholder="Tell us a bit about yourself..."
						rows="3"
						class="w-full rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 px-4 py-2.5 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
					></textarea>
				</div>
				<div class="grid grid-cols-2 gap-4">
					<Input label="Education Level" bind:value={educationLevel} placeholder="e.g. B.Tech, Class 12" />
					<Input label="Exam Target" bind:value={examTarget} placeholder="e.g. UPSC, GATE, JEE" />
				</div>
				<Button type="submit" loading={savingProfile} disabled={savingProfile}>
					<Save class="h-4 w-4" /> Save Changes
				</Button>
			</form>
		</Card>

		<!-- Change password -->
		{#if $currentUser?.profile !== null}
			<Card padding="lg">
				<div class="flex items-center gap-3 mb-6">
					<div class="h-9 w-9 rounded-xl bg-orange-100 dark:bg-orange-900/30 flex items-center justify-center">
						<Lock class="h-5 w-5 text-orange-600 dark:text-orange-400" />
					</div>
					<div>
						<h2 class="font-semibold text-gray-900 dark:text-white">Change Password</h2>
						<p class="text-sm text-gray-500 dark:text-gray-400">Update your account password</p>
					</div>
				</div>

				<form on:submit|preventDefault={changePassword} class="space-y-4">
					<Input type="password" label="Current Password" bind:value={currentPassword} placeholder="••••••••" />
					<Input type="password" label="New Password" bind:value={newPassword} placeholder="••••••••" />
					<Input type="password" label="Confirm New Password" bind:value={confirmPassword} placeholder="••••••••" />
					<Button type="submit" loading={changingPassword} disabled={changingPassword} variant="secondary">
						Update Password
					</Button>
				</form>
			</Card>
		{/if}

		<!-- Danger zone -->
		<Card padding="lg" class="border-red-100 dark:border-red-900">
			<div class="flex items-center gap-3 mb-4">
				<div class="h-9 w-9 rounded-xl bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
					<Trash2 class="h-5 w-5 text-red-600 dark:text-red-400" />
				</div>
				<div>
					<h2 class="font-semibold text-red-600 dark:text-red-400">Danger Zone</h2>
					<p class="text-sm text-gray-500 dark:text-gray-400">Irreversible actions</p>
				</div>
			</div>
			<p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
				Deleting your account will permanently remove all your data including summaries, quizzes, and history. This cannot be undone.
			</p>
			{#if !showDeleteConfirm}
				<Button variant="danger" on:click={() => showDeleteConfirm = true}>Delete Account</Button>
			{:else}
				<div class="rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-4 space-y-3">
					<p class="text-sm font-medium text-red-700 dark:text-red-300">Are you absolutely sure?</p>
					<div class="flex gap-2">
						<Button variant="danger" on:click={deleteAccount} size="sm">Yes, delete my account</Button>
						<Button variant="secondary" on:click={() => showDeleteConfirm = false} size="sm">Cancel</Button>
					</div>
				</div>
			{/if}
		</Card>
	</div>
</PageLayout>
