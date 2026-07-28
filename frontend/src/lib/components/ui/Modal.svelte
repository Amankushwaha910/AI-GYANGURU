<script lang="ts">
	import { cn } from '$lib/utils';
	import { X } from 'lucide-svelte';
	export let open = false;
	export let title: string = '';
	export let maxWidth: string = 'max-w-lg';

	function close() { open = false; }
	function handleKey(e: KeyboardEvent) { if (e.key === 'Escape') close(); }
</script>

{#if open}
	<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
	<div
		role="dialog"
		aria-modal="true"
		aria-label={title}
		class="fixed inset-0 z-50 flex items-center justify-center p-4"
		on:keydown={handleKey}
	>
		<!-- Backdrop -->
		<button
			class="absolute inset-0 bg-black/50 backdrop-blur-sm"
			on:click={close}
			aria-label="Close modal"
		/>

		<!-- Panel -->
		<div
			class={cn(
				'relative z-10 w-full rounded-2xl bg-white p-6 shadow-2xl animate-slide-up',
				'dark:bg-gray-900 dark:border dark:border-gray-800',
				maxWidth
			)}
		>
			{#if title}
				<div class="flex items-center justify-between mb-5">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-white">{title}</h2>
					<button
						on:click={close}
						class="rounded-lg p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
						aria-label="Close"
					>
						<X class="h-5 w-5" />
					</button>
				</div>
			{/if}
			<slot />
		</div>
	</div>
{/if}
