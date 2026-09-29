<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { filesApi } from '$api/files';
	import { toast } from '$stores/toast';
	import type { Upload } from '$types';
	import { formatFileSize, formatRelativeTime } from '$lib/utils';
	import Button from '$components/ui/Button.svelte';
	import Card from '$components/ui/Card.svelte';
	import Skeleton from '$components/ui/Skeleton.svelte';
	import Badge from '$components/ui/Badge.svelte';
	import EmptyState from '$components/ui/EmptyState.svelte';
	import PageLayout from '$components/layout/PageLayout.svelte';
	import {
		Upload as UploadIcon, FileText, Image, Trash2,
		CheckCircle, Clock, AlertCircle, Loader, RefreshCw
	} from 'lucide-svelte';

	let uploads: Upload[] = [];
	let loading = true;
	let uploading = false;
	let dragOver = false;
	let fileInput: HTMLInputElement;
	let deletingId: string | null = null;

	// IDs of uploads currently being polled (pending or processing)
	let pollingIds = new Set<string>();
	let pollTimer: ReturnType<typeof setInterval> | null = null;

	const ALLOWED = ['pdf', 'docx', 'txt', 'png', 'jpg', 'jpeg', 'webp'];
	const POLL_INTERVAL_MS = 3000; // poll every 3 s (was 2.5 s)

	onMount(() => loadUploads());
	onDestroy(() => stopPolling());

	// ── Data loading ────────────────────────────────────────────────────────────

	async function loadUploads() {
		loading = true;
		try {
			const res = await filesApi.list({ page: 1, page_size: 20 });
			uploads = res.data;
			// Start polling any in-progress uploads from previous sessions
			startPollingForInProgress();
		} catch (e: any) {
			toast.error('Failed to load uploads: ' + (e?.message ?? 'Unknown error'));
		} finally {
			loading = false;
		}
	}

	// ── Polling ─────────────────────────────────────────────────────────────────

	function startPollingForInProgress() {
		const inProgress = uploads
			.filter(u => u.status === 'pending' || u.status === 'processing')
			.map(u => u.id);

		if (inProgress.length === 0) return;

		inProgress.forEach(id => pollingIds.add(id));
		ensurePollTimer();
	}

	function ensurePollTimer() {
		if (pollTimer !== null) return; // already running
		pollTimer = setInterval(pollInProgress, POLL_INTERVAL_MS);
	}

	function stopPolling() {
		if (pollTimer !== null) {
			clearInterval(pollTimer);
			pollTimer = null;
		}
		pollingIds.clear();
	}

	async function pollInProgress() {
		if (pollingIds.size === 0) {
			stopPolling();
			return;
		}

		const ids = [...pollingIds];
		const results = await Promise.allSettled(
			ids.map(id => filesApi.get(id))
		);

		results.forEach((result, i) => {
			const id = ids[i];
			if (result.status !== 'fulfilled') return;

			const updated = result.value.data;
			if (!updated) return;

			// Update the upload in the list
			uploads = uploads.map(u => (u.id === id ? { ...u, ...updated } : u));

			// If no longer in-progress, stop polling this ID
			if (updated.status !== 'pending' && updated.status !== 'processing') {
				pollingIds.delete(id);

				if (updated.status === 'completed') {
					toast.success(`"${updated.original_filename}" is ready to use!`);
				} else if (updated.status === 'failed') {
					toast.error(
						`Processing failed for "${updated.original_filename}": ` +
						(updated.error_message ?? 'Unknown error')
					);
				}
			}
		});

		// Reactivity trigger
		pollingIds = new Set(pollingIds);

		if (pollingIds.size === 0) stopPolling();
	}

	// ── Upload ──────────────────────────────────────────────────────────────────

	async function handleUpload(file: File) {
		const ext = file.name.split('.').pop()?.toLowerCase() ?? '';
		if (!ALLOWED.includes(ext)) {
			toast.error(`File type .${ext} is not supported. Allowed: ${ALLOWED.join(', ')}`);
			return;
		}
		if (file.size > 20 * 1024 * 1024) {
			toast.error('File exceeds the 20 MB limit');
			return;
		}
		if (file.size === 0) {
			toast.error('The selected file is empty');
			return;
		}

		uploading = true;
		try {
			const res = await filesApi.upload(file);
			if (res.data) {
				uploads = [res.data, ...uploads];
				toast.success(`"${file.name}" uploaded — extracting content…`);
				// Start polling immediately for this new upload
				pollingIds.add(res.data.id);
				ensurePollTimer();
			}
		} catch (e: any) {
			const msg = e?.message ?? 'Upload failed';
			toast.error(msg);
		} finally {
			uploading = false;
			// Reset file input so the same file can be re-selected
			if (fileInput) fileInput.value = '';
		}
	}

	function onFileInput(e: Event) {
		const f = (e.target as HTMLInputElement).files?.[0];
		if (f) handleUpload(f);
	}

	function onDrop(e: DragEvent) {
		dragOver = false;
		const f = e.dataTransfer?.files[0];
		if (f) handleUpload(f);
	}

	// ── Delete ──────────────────────────────────────────────────────────────────

	async function deleteUpload(id: string) {
		deletingId = id;
		try {
			await filesApi.delete(id);
			uploads = uploads.filter(u => u.id !== id);
			pollingIds.delete(id);
			toast.success('File deleted');
		} catch {
			toast.error('Failed to delete file');
		} finally {
			deletingId = null;
		}
	}

	// ── Status display ──────────────────────────────────────────────────────────

	const statusConfig: Record<string, { icon: any; color: string; bg: string; label: string; spin?: boolean }> = {
		completed: {
			icon: CheckCircle,
			color: 'text-green-600 dark:text-green-400',
			bg: 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800',
			label: 'Ready'
		},
		processing: {
			icon: Loader,
			color: 'text-blue-500 dark:text-blue-400',
			bg: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800',
			label: 'Extracting content…',
			spin: true
		},
		pending: {
			icon: Clock,
			color: 'text-amber-500 dark:text-amber-400',
			bg: 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800',
			label: 'Queued…',
			spin: false
		},
		failed: {
			icon: AlertCircle,
			color: 'text-red-500 dark:text-red-400',
			bg: 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800',
			label: 'Failed'
		}
	};

	const fileIcons: Record<string, any> = {
		pdf: FileText, docx: FileText, txt: FileText,
		png: Image, jpg: Image, jpeg: Image, webp: Image
	};

	$: activePolling = pollingIds.size > 0;
</script>

<svelte:head><title>Upload — AI GyanGuru</title></svelte:head>

<PageLayout title="File Upload" subtitle="Upload PDFs, documents, or images — AI will extract and study the content">

	<!-- ── Drop zone ──────────────────────────────────────────────────────── -->
	<div
		class="mb-8 rounded-2xl border-2 border-dashed transition-all duration-200 {
			dragOver
				? 'border-brand-500 bg-brand-50 dark:bg-brand-900/10 scale-[1.01]'
				: 'border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900'
		}"
		on:dragover|preventDefault={() => (dragOver = true)}
		on:dragleave={() => (dragOver = false)}
		on:drop|preventDefault={onDrop}
		role="region"
		aria-label="File drop zone"
	>
		<div class="flex flex-col items-center justify-center py-14 px-6 text-center">
			<div
				class="mb-4 h-14 w-14 rounded-2xl flex items-center justify-center transition-colors {
					dragOver ? 'bg-brand-100 dark:bg-brand-900/30' : 'bg-gray-100 dark:bg-gray-800'
				}"
			>
				{#if uploading}
					<Loader class="h-7 w-7 text-brand-500 animate-spin" />
				{:else}
					<UploadIcon class="h-7 w-7 {dragOver ? 'text-brand-600' : 'text-gray-400'}" />
				{/if}
			</div>

			<p class="text-base font-semibold text-gray-700 dark:text-gray-300 mb-1">
				{#if uploading}
					Uploading…
				{:else if dragOver}
					Drop your file here
				{:else}
					Drag & drop or click to upload
				{/if}
			</p>
			<p class="text-sm text-gray-400 dark:text-gray-500 mb-5">
				PDF, DOCX, TXT, PNG, JPG, WEBP · Max 20 MB
			</p>

			<Button
				on:click={() => fileInput.click()}
				loading={uploading}
				disabled={uploading}
			>
				{uploading ? 'Uploading…' : 'Choose File'}
			</Button>

			<input
				bind:this={fileInput}
				type="file"
				class="hidden"
				accept=".pdf,.docx,.txt,.png,.jpg,.jpeg,.webp"
				on:change={onFileInput}
			/>
		</div>
	</div>

	<!-- ── How it works ───────────────────────────────────────────────────── -->
	<div class="mb-8 rounded-xl bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800 p-4">
		<p class="text-sm font-semibold text-blue-700 dark:text-blue-300 mb-2">📋 How file processing works</p>
		<div class="flex flex-wrap gap-3 text-xs text-blue-600 dark:text-blue-400">
			<span class="flex items-center gap-1.5">
				<span class="h-5 w-5 rounded-full bg-blue-200 dark:bg-blue-800 flex items-center justify-center text-[10px] font-bold">1</span>
				Upload file
			</span>
			<span class="text-blue-300">→</span>
			<span class="flex items-center gap-1.5">
				<span class="h-5 w-5 rounded-full bg-blue-200 dark:bg-blue-800 flex items-center justify-center text-[10px] font-bold">2</span>
				Extract text content
			</span>
			<span class="text-blue-300">→</span>
			<span class="flex items-center gap-1.5">
				<span class="h-5 w-5 rounded-full bg-blue-200 dark:bg-blue-800 flex items-center justify-center text-[10px] font-bold">3</span>
				Status → Ready
			</span>
			<span class="text-blue-300">→</span>
			<span class="flex items-center gap-1.5">
				<span class="h-5 w-5 rounded-full bg-blue-200 dark:bg-blue-800 flex items-center justify-center text-[10px] font-bold">4</span>
				Generate Summary / Quiz / Explanation from content
			</span>
		</div>
	</div>

	<!-- ── File list ──────────────────────────────────────────────────────── -->
	<div>
		<div class="flex items-center justify-between mb-4">
			<h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
				Your Files
				{#if activePolling}
					<span class="ml-2 inline-flex items-center gap-1 text-blue-500 dark:text-blue-400 normal-case font-normal">
						<RefreshCw class="h-3 w-3 animate-spin" />
						<span>Updating…</span>
					</span>
				{/if}
			</h3>
			<button
				on:click={loadUploads}
				class="text-xs text-gray-400 hover:text-brand-600 dark:hover:text-brand-400 transition-colors flex items-center gap-1"
				title="Refresh list"
				disabled={loading}
			>
				<RefreshCw class="h-3.5 w-3.5 {loading ? 'animate-spin' : ''}" />
				Refresh
			</button>
		</div>

		{#if loading}
			<div class="space-y-3">
				{#each Array(4) as _}
					<div class="flex gap-3 p-4 rounded-xl border border-gray-100 dark:border-gray-800">
						<Skeleton height="h-10" width="w-10" rounded="rounded-xl" />
						<div class="flex-1 space-y-2">
							<Skeleton height="h-4" width="w-1/2" />
							<Skeleton height="h-3" width="w-1/4" />
						</div>
					</div>
				{/each}
			</div>

		{:else if uploads.length === 0}
			<EmptyState
				icon={UploadIcon}
				title="No files uploaded yet"
				description="Upload study materials to generate summaries, explanations, and quizzes from them."
			/>

		{:else}
			<!-- 2-column grid on md+, single column on mobile -->
			<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
				{#each uploads as upload (upload.id)}
					{@const status = statusConfig[upload.status] ?? statusConfig.pending}
					{@const FileIcon = fileIcons[upload.file_type] ?? FileText}
					{@const isInProgress = upload.status === 'pending' || upload.status === 'processing'}

					<div
						class="rounded-2xl border bg-white dark:bg-gray-900 transition-shadow hover:shadow-sm flex flex-col
						       {isInProgress ? 'border-blue-200 dark:border-blue-800' : 'border-gray-200 dark:border-gray-800'}
						       group"
					>
						<!-- Card header -->
						<div class="flex items-start gap-3 p-4">
							<!-- File icon -->
							<div class="h-10 w-10 rounded-xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center flex-shrink-0 mt-0.5">
								<svelte:component this={FileIcon} class="h-5 w-5 text-gray-500 dark:text-gray-400" />
							</div>

							<!-- File info + status -->
							<div class="flex-1 min-w-0">
								<p class="text-sm font-semibold text-gray-800 dark:text-gray-200 truncate">
									{upload.original_filename}
								</p>
								<p class="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
									{formatFileSize(upload.file_size_bytes)} · {upload.file_type.toUpperCase()}
									{#if upload.ocr_used} · OCR{/if}
								</p>
								<div class="flex items-center gap-1.5 mt-1.5">
									<svelte:component
										this={status.icon}
										class="h-3.5 w-3.5 {status.color} {status.spin ? 'animate-spin' : ''}"
									/>
									<span class="text-xs font-medium {status.color}">
										{status.label}
									</span>
								</div>
							</div>

							<!-- Delete -->
							<button
								on:click={() => deleteUpload(upload.id)}
								disabled={deletingId === upload.id}
								class="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg
								       text-gray-400 hover:text-red-500 hover:bg-red-50
								       dark:hover:bg-red-900/20 transition-all disabled:opacity-30 flex-shrink-0"
								title="Delete"
								aria-label="Delete {upload.original_filename}"
							>
								<Trash2 class="h-4 w-4" />
							</button>
						</div>

						<!-- Progress bar -->
						{#if isInProgress}
							<div class="px-4 pb-3">
								<div class="flex items-center gap-2">
									<div class="flex-1 h-1.5 rounded-full bg-gray-100 dark:bg-gray-800 overflow-hidden">
										<div class="h-full rounded-full bg-blue-400 dark:bg-blue-500
										            {upload.status === 'processing' ? 'animate-progress' : 'w-1/4'}">
										</div>
									</div>
									<span class="text-xs text-blue-500 flex-shrink-0">
										{upload.status === 'processing' ? 'Extracting…' : 'Queued…'}
									</span>
								</div>
							</div>
						{:else if upload.status === 'failed' && upload.error_message}
							<div class="mx-4 mb-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 px-3 py-2">
								<p class="text-xs text-red-600 dark:text-red-400 leading-snug">
									<span class="font-medium">Error:</span> {upload.error_message}
								</p>
							</div>
						{/if}

						<!-- Action buttons at bottom of card -->
						{#if upload.status === 'completed'}
							<div class="flex gap-2 px-4 pb-4 pt-1 border-t border-gray-100 dark:border-gray-800 mt-auto">
								<a
									href="/summary?upload_id={upload.id}"
									class="flex-1 text-center text-xs font-medium py-1.5 rounded-lg
									       bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300
									       hover:bg-blue-100 dark:hover:bg-blue-900/40 transition-colors"
								>
									Summary
								</a>
								<a
									href="/explanation?upload_id={upload.id}"
									class="flex-1 text-center text-xs font-medium py-1.5 rounded-lg
									       bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300
									       hover:bg-purple-100 dark:hover:bg-purple-900/40 transition-colors"
								>
									Explain
								</a>
								<a
									href="/quiz?upload_id={upload.id}"
									class="flex-1 text-center text-xs font-medium py-1.5 rounded-lg
									       bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300
									       hover:bg-green-100 dark:hover:bg-green-900/40 transition-colors"
								>
									Quiz
								</a>
							</div>
						{/if}
					</div>
				{/each}
			</div>
		{/if}
	</div>
</PageLayout>

<style>
	@keyframes progress-bar {
		0%   { width: 15%; }
		50%  { width: 80%; }
		100% { width: 15%; }
	}
	.animate-progress {
		animation: progress-bar 2s ease-in-out infinite;
	}
</style>
