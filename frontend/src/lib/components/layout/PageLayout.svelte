<script lang="ts">
	export let title: string = '';
	export let subtitle: string = '';
</script>

<div class="flex-1 overflow-y-auto">
	{#if title}
		<header class="px-8 py-6 border-b border-gray-100 dark:border-gray-800">
			<h1 class="text-2xl font-bold text-gray-900 dark:text-white">{title}</h1>
			{#if subtitle}
				<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">{subtitle}</p>
			{/if}
		</header>
	{/if}
	<main class="px-8 py-6">
		<slot />
	</main>
</div>
