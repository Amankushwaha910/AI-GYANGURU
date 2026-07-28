<script lang="ts">
	import { cn } from '$lib/utils';
	export let height: string = 'h-4';
	export let width: string = 'w-full';
	export let rounded: string = 'rounded-lg';
	let className = '';
	export { className as class };
</script>

<div
	class={cn(
		'animate-pulse bg-gray-200 dark:bg-gray-700',
		height,
		width,
		rounded,
		className
	)}
/>
