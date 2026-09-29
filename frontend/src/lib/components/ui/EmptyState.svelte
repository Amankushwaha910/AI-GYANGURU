<script lang="ts">
	export let icon: any = null;
	export let title: string = 'Nothing here yet';
	export let description: string = '';
</script>

<div class="empty-state animate-fade-in-up">
	{#if icon}
		<div class="empty-state-icon">
			<svelte:component this={icon} class="h-7 w-7 text-gray-400 dark:text-gray-500" />
		</div>
	{/if}
	<h3 class="text-base font-semibold text-gray-700 dark:text-gray-300">{title}</h3>
	{#if description}
		<p class="mt-1.5 text-sm text-gray-500 dark:text-gray-400 max-w-sm leading-relaxed">
			{description}
		</p>
	{/if}
	<div class="mt-5">
		<slot />
	</div>
</div>
