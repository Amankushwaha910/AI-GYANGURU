<script lang="ts">
	export let title: string = '';
	export let subtitle: string = '';
</script>

<header class="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-800 bg-white dark:bg-gray-950">
	<div>
		{#if title}
			<h1 class="text-xl font-bold text-gray-900 dark:text-white">{title}</h1>
		{/if}
		{#if subtitle}
			<p class="text-sm text-gray-500 dark:text-gray-400 mt-0.5">{subtitle}</p>
		{/if}
	</div>
	<slot />
</header>
