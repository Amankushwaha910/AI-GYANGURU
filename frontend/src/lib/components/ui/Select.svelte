<script lang="ts">
	import { cn } from '$lib/utils';
	export let value: string = '';
	export let label: string = '';
	export let options: { value: string; label: string }[] = [];
	export let disabled = false;
	export let id: string = '';
	let className = '';
	export { className as class };

	$: selectId = id || label.toLowerCase().replace(/\s+/g, '-') || 'select-' + Math.random().toString(36).slice(2);
</script>

<div class={cn('flex flex-col gap-1.5', className)}>
	{#if label}
		<label for={selectId} class="text-sm font-medium text-gray-700 dark:text-gray-300">{label}</label>
	{/if}
	<select
		id={selectId}
		bind:value
		{disabled}
		on:change
		class="h-10 w-full rounded-xl border border-gray-300 bg-white px-3 text-sm text-gray-900
		       focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent
		       disabled:opacity-50 dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100"
	>
		{#each options as opt}
			<option value={opt.value}>{opt.label}</option>
		{/each}
	</select>
</div>
