<script lang="ts">
	import { onMount } from 'svelte';
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
	import { Upload as UploadIcon, FileText, Image, Trash2, CheckCircle, Clock, AlertCircle, X } from 'lucide-svelte';

	let uploads: Upload[] = [];
	let loading = true;
	let uploading = false;
	let dragOver = false;
	let fileInput: HTMLInputElement;
	let deletingId: string | null = null;

	const ALLOWED = ['pdf', 'docx', 'txt', 'png', 'jpg', 'jpeg', 'webp'];

	onMount(() => loadUploads());

	async function loadUploads() {
		loading = true;
		try {
			const res = await filesApi.list({ page: 1, page_size: 20 });
			uploads = res.data;
		} finally { loading = false; }
	}

	async function handleUpload(file: File) {
		const ext = file.name.split('.').pop()?.toLowerCase() ?? '';
		if (!ALLOWED.includes(ext)) { toast.error(`File type .${ext} is not supported`); return; }
		if (file.size > 20 * 1024 * 1024) { toast.error('File exceeds 20MB limit'); return; }

		uploading = true;
		try {
			const res = await filesApi.upload(file);
			if (res.data) {
				uploads = [res.data, ...uploads];
				toast.success('File uploaded! Text extraction in progress...');
			}
		} catch (e: any) {
			toast.error(e.message ?? 'Upload failed');
		} finally { uploading = false; }
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

	async function deleteUpload(id: string) {
		deletingId = id;
		try {
			await filesApi.delete(id);
			uploads = uploads.filter(u => u.id !== id);
			toast.success('File deleted');
		} catch { toast.error('Failed to delete file'); }
		finally { deletingId = null; }
	}

	const statusConfig = {
		completed: { icon: CheckCircle, color: 'text-green-500', label: 'Ready' },
		processing: { icon: Clock, color: 'text-yellow-500', label: 'Processing' },
		pending: { icon: Clock, color: 'text-gray-400', label: 'Pending' },
		failed: { icon: AlertCircle, color: 'text-red-500', label: 'Failed' }
	};

	const fileIcons: Record<string, any> = {
		pdf: FileText, docx: FileText, txt: FileText,
		png: Image, jpg: Image, jpeg: Image, webp: Image
	};
</script>

<svelte:head><title>Upload — AI GyanGuru</title></svelte:head>

<PageLayout title="File Upload" subtitle="Upload PDFs, documents, or images and study from them">
	<!-- Drop zone -->
	<div
		class="mb-8 rounded-2xl border-2 border-dashed transition-all duration-200 {
			dragOver ? 'border-brand-500 bg-brand-50 dark:bg-brand-900/10' : 'border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900'
		}"
		on:dragover|preventDefault={() => dragOver = true}
		on:dragleave={() => dragOver = false}
		on:drop|preventDefault={onDrop}
		role="region"
		aria-label="File drop zone"
	>
		<div class="flex flex-col items-center justify-center py-14 px-6 text-center">
			<div class="mb-4 h-14 w-14 rounded-2xl {dragOver ? 'bg-brand-100 dark:bg-brand-900/30' : 'bg-gray-100 dark:bg-gray-800'} flex items-center justify-center transition-colors">
				<UploadIcon class="h-7 w-7 {dragOver ? 'text-brand-600' : 'text-gray-400'}" />
			</div>
			<p class="text-base font-semibold text-gray-700 dark:text-gray-300 mb-1">
				{dragOver ? 'Drop your file here' : 'Drag & drop or click to upload'}
			</p>
			<p class="text-sm text-gray-400 dark:text-gray-500 mb-5">
				PDF, DOCX, TXT, PNG, JPG, WEBP · Max 20MB
			</p>
			<Button on:click={() => fileInput.click()} loading={uploading} disabled={uploading}>
				{uploading ? 'Uploading...' : 'Choose File'}
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

	<!-- Uploaded files -->
	<div>
		<h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4">Your Files</h3>

		{#if loading}
			<div class="space-y-3">
				{#each Array(4) as _}
					<div class="flex gap-3 p-4 rounded-xl border border-gray-100 dark:border-gray-800">
						<Skeleton height="h-10" width="w-10" rounded="rounded-xl" />
						<div class="flex-1 space-y-2"><Skeleton height="h-4" width="w-1/2" /><Skeleton height="h-3" width="w-1/4" /></div>
					</div>
				{/each}
			</div>
		{:else if uploads.length === 0}
			<EmptyState icon={UploadIcon} title="No files uploaded yet" description="Upload study materials to generate summaries, explanations, and quizzes from them." />
		{:else}
			<div class="space-y-3">
				{#each uploads as upload (upload.id)}
					{@const status = statusConfig[upload.status]}
					{@const FileIcon = fileIcons[upload.file_type] ?? FileText}
					<div class="flex items-center gap-4 p-4 rounded-xl border border-gray-100 dark:border-gray-800 bg-white dark:bg-gray-900 group hover:shadow-sm transition-shadow">
						<div class="h-10 w-10 rounded-xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center flex-shrink-0">
							<svelte:component this={FileIcon} class="h-5 w-5 text-gray-500 dark:text-gray-400" />
						</div>
						<div class="flex-1 min-w-0">
							<p class="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">{upload.original_filename}</p>
							<p class="text-xs text-gray-400 dark:text-gray-500">
								{formatFileSize(upload.file_size_bytes)} · {upload.file_type.toUpperCase()}
								{#if upload.ocr_used} · OCR{/if}
								· {formatRelativeTime(upload.created_at)}
							</p>
						</div>
						<div class="flex items-center gap-2">
							<div class="flex items-center gap-1">
								<svelte:component this={status.icon} class="h-4 w-4 {status.color}" />
								<span class="text-xs font-medium {status.color} hidden sm:inline">{status.label}</span>
							</div>
							{#if upload.status === 'completed'}
								<div class="flex gap-1">
									<Button href="/summary" variant="ghost" size="sm" class="text-xs hidden sm:flex">Summary</Button>
									<Button href="/quiz" variant="ghost" size="sm" class="text-xs hidden sm:flex">Quiz</Button>
								</div>
							{/if}
							<button
								on:click={() => deleteUpload(upload.id)}
								disabled={deletingId === upload.id}
								class="opacity-0 group-hover:opacity-100 p-2 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-all"
								title="Delete file"
							>
								<Trash2 class="h-4 w-4" />
							</button>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</div>
</PageLayout>
