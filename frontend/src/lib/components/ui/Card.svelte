<script lang="ts">
	import { cn } from '$lib/utils';
	export let hoverable = false;
	export let padding: 'none' | 'sm' | 'md' | 'lg' = 'md';
	let className = '';
	export { className as class };

	const paddings = { none: '', sm: 'p-4', md: 'p-6', lg: 'p-8' };
</script>

<div
	class={cn(
		'rounded-2xl border bg-white shadow-sm transition-all duration-200',
		'dark:bg-gray-900 dark:border-gray-800',
		hoverable && 'hover:shadow-md hover:-translate-y-0.5 cursor-pointer',
		paddings[padding],
		className
	)}
>
	<slot />
</div>
