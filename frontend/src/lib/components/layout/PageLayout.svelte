<script lang="ts">
	export let title: string = '';
	export let subtitle: string = '';
</script>

<!--
  PageLayout — wraps every authenticated page.
  Uses .page-container to cap content at 1280 px on wide screens,
  while staying full-width on laptops and below.
-->
<div class="flex-1 overflow-y-auto">
	{#if title}
		<div class="border-b border-gray-100 dark:border-gray-800 bg-white dark:bg-gray-950">
			<header class="page-container px-8 py-5">
				<h1 class="page-title">{title}</h1>
				{#if subtitle}
					<p class="page-subtitle">{subtitle}</p>
				{/if}
			</header>
		</div>
	{/if}

	<main class="page-container px-8 py-7">
		<slot />
	</main>
</div>
