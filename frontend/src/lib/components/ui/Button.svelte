<script lang="ts">
	import { cn } from '$lib/utils';

	export let variant: 'primary' | 'secondary' | 'ghost' | 'danger' | 'outline' = 'primary';
	export let size: 'sm' | 'md' | 'lg' = 'md';
	export let loading = false;
	export let disabled = false;
	export let type: 'button' | 'submit' | 'reset' = 'button';
	export let href: string | undefined = undefined;
	let className = '';
	export { className as class };

	const base =
		'inline-flex items-center justify-center gap-2 font-medium rounded-xl transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 active:scale-95';

	const variants = {
		primary:
			'bg-brand-600 text-white hover:bg-brand-700 shadow-sm hover:shadow-md dark:bg-brand-500 dark:hover:bg-brand-600',
		secondary:
			'bg-gray-100 text-gray-900 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-100 dark:hover:bg-gray-700',
		ghost:
			'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800',
		danger:
			'bg-red-600 text-white hover:bg-red-700 shadow-sm dark:bg-red-500 dark:hover:bg-red-600',
		outline:
			'border-2 border-brand-600 text-brand-600 hover:bg-brand-50 dark:border-brand-400 dark:text-brand-400 dark:hover:bg-brand-950'
	};

	const sizes = {
		sm: 'h-8 px-3 text-sm',
		md: 'h-10 px-5 text-sm',
		lg: 'h-12 px-7 text-base'
	};
</script>

{#if href}
	<a
		{href}
		class={cn(base, variants[variant], sizes[size], className)}
		aria-disabled={disabled}
	>
		{#if loading}
			<svg class="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
				<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
				<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
			</svg>
		{/if}
		<slot />
	</a>
{:else}
	<button
		{type}
		{disabled}
		class={cn(base, variants[variant], sizes[size], className)}
		on:click
		on:submit
	>
		{#if loading}
			<svg class="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
				<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
				<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
			</svg>
		{/if}
		<slot />
	</button>
{/if}
