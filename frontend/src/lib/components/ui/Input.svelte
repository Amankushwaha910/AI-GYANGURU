<script lang="ts">
	import { cn } from '$lib/utils';

	export let type: 'text' | 'email' | 'password' | 'number' | 'search' | 'tel' | 'url' = 'text';
	export let value: string = '';
	export let placeholder: string = '';
	export let label: string = '';
	export let error: string = '';
	export let disabled = false;
	export let required = false;
	export let name: string = '';
	export let id: string = '';
	let className = '';
	export { className as class };

	$: inputId = id || name || label.toLowerCase().replace(/\s+/g, '-') || 'input';

	const inputClass = (err: string) => cn(
		'h-10 w-full rounded-xl border bg-white px-4 text-sm text-gray-900 placeholder-gray-400 transition-colors',
		'focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent',
		'disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-gray-50',
		'dark:bg-gray-900 dark:text-gray-100 dark:placeholder-gray-500',
		'dark:focus:ring-brand-400',
		err ? 'border-red-500 focus:ring-red-500' : 'border-gray-300 dark:border-gray-700'
	);
</script>

<div class={cn('flex flex-col gap-1.5', className)}>
	{#if label}
		<label for={inputId} class="text-sm font-medium text-gray-700 dark:text-gray-300">
			{label}{#if required}<span class="text-red-500 ml-0.5">*</span>{/if}
		</label>
	{/if}

	{#if type === 'password'}
		<input
			type="password"
			id={inputId}
			{name}
			{placeholder}
			{disabled}
			{required}
			bind:value
			on:change
			on:blur
			class={inputClass(error)}
		/>
	{:else if type === 'email'}
		<input
			type="email"
			id={inputId}
			{name}
			{placeholder}
			{disabled}
			{required}
			bind:value
			on:change
			on:blur
			class={inputClass(error)}
		/>
	{:else if type === 'number'}
		<input
			type="number"
			id={inputId}
			{name}
			{placeholder}
			{disabled}
			{required}
			bind:value
			on:change
			on:blur
			class={inputClass(error)}
		/>
	{:else}
		<input
			type="text"
			id={inputId}
			{name}
			{placeholder}
			{disabled}
			{required}
			bind:value
			on:change
			on:blur
			class={inputClass(error)}
		/>
	{/if}

	{#if error}
		<p class="text-xs text-red-600 dark:text-red-400">{error}</p>
	{/if}
</div>
