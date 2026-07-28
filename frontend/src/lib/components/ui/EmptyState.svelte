<script lang="ts">
	export let icon: any = null;
	export let title: string = 'Nothing here yet';
	export let description: string = '';
</script>

<div class="flex flex-col items-center justify-center py-16 px-4 text-center">
	{#if icon}
		<div class="mb-4 rounded-full bg-gray-100 p-4 dark:bg-gray-800">
			<svelte:component this={icon} class="h-8 w-8 text-gray-400 dark:text-gray-500" />
		</div>
	{/if}
	<h3 class="text-base font-semibold text-gray-700 dark:text-gray-300">{title}</h3>
	{#if description}
		<p class="mt-1 text-sm text-gray-500 dark:text-gray-400 max-w-xs">{description}</p>
	{/if}
	<div class="mt-4">
		<slot />
	</div>
</div>
