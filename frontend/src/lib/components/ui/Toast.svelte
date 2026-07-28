<script lang="ts">
	import { toast } from '$stores/toast';
	import { CheckCircle, XCircle, Info, AlertTriangle, X } from 'lucide-svelte';
	import { cn } from '$lib/utils';

	const icons = {
		success: CheckCircle,
		error: XCircle,
		info: Info,
		warning: AlertTriangle
	};

	const styles = {
		success: 'bg-green-50 border-green-200 text-green-800 dark:bg-green-900/20 dark:border-green-800 dark:text-green-300',
		error: 'bg-red-50 border-red-200 text-red-800 dark:bg-red-900/20 dark:border-red-800 dark:text-red-300',
		info: 'bg-blue-50 border-blue-200 text-blue-800 dark:bg-blue-900/20 dark:border-blue-800 dark:text-blue-300',
		warning: 'bg-yellow-50 border-yellow-200 text-yellow-800 dark:bg-yellow-900/20 dark:border-yellow-800 dark:text-yellow-300'
	};
</script>

<div class="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 max-w-sm w-full">
	{#each $toast as t (t.id)}
		<div
			class={cn(
				'flex items-start gap-3 rounded-xl border p-4 shadow-lg animate-slide-up',
				styles[t.type]
			)}
			role="alert"
		>
			<svelte:component this={icons[t.type]} class="h-5 w-5 mt-0.5 flex-shrink-0" />
			<p class="text-sm font-medium flex-1">{t.message}</p>
			<button
				on:click={() => toast.remove(t.id)}
				class="opacity-60 hover:opacity-100 transition-opacity"
				aria-label="Dismiss"
			>
				<X class="h-4 w-4" />
			</button>
		</div>
	{/each}
</div>
