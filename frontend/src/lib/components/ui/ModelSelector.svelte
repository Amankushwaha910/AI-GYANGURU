<script lang="ts">
	import { onMount } from 'svelte';
	import { modelSelector, selectedModel, availableProviders, modelsLoading } from '$stores/modelSelector';
	import { modelsApi } from '$api/models';
	import { ChevronDown, Cpu, AlertCircle, Loader } from 'lucide-svelte';

	let open = false;
	let containerEl: HTMLDivElement;

	onMount(() => {
		// Load models once if not already loaded
		if ($availableProviders.length === 0) {
			modelSelector.load(modelsApi);
		}

		// Close dropdown on outside click
		function handleClick(e: MouseEvent) {
			if (containerEl && !containerEl.contains(e.target as Node)) {
				open = false;
			}
		}
		document.addEventListener('click', handleClick);
		return () => document.removeEventListener('click', handleClick);
	});

	function select(provider: string, modelId: string, providerDisplay: string, modelDisplay: string) {
		modelSelector.select(provider, modelId, `${providerDisplay} — ${modelDisplay}`);
		open = false;
	}
</script>

<div class="relative" bind:this={containerEl}>
	<!-- Trigger button -->
	<button
		type="button"
		on:click={() => open = !open}
		class="flex items-center gap-2 rounded-xl border border-gray-200 dark:border-gray-700
		       bg-white dark:bg-gray-900 px-3 py-2 text-sm font-medium text-gray-700
		       dark:text-gray-300 hover:border-brand-400 dark:hover:border-brand-500
		       focus:outline-none focus:ring-2 focus:ring-brand-500 transition-all
		       min-w-[200px] max-w-[280px]"
		aria-haspopup="listbox"
		aria-expanded={open}
	>
		<Cpu class="h-4 w-4 flex-shrink-0 text-brand-500" />
		<span class="flex-1 truncate text-left">
			{#if $modelsLoading}
				<span class="text-gray-400">Loading models…</span>
			{:else if $selectedModel}
				{$selectedModel.display}
			{:else if $availableProviders.length === 0}
				<span class="text-gray-400">No AI configured</span>
			{:else}
				Select AI Model
			{/if}
		</span>
		{#if $modelsLoading}
			<Loader class="h-3.5 w-3.5 animate-spin text-gray-400 flex-shrink-0" />
		{:else}
			<ChevronDown class="h-4 w-4 flex-shrink-0 text-gray-400 transition-transform {open ? 'rotate-180' : ''}" />
		{/if}
	</button>

	<!-- Dropdown panel -->
	{#if open && !$modelsLoading}
		<div
			class="absolute left-0 top-full mt-1.5 z-50 w-72 rounded-2xl border border-gray-200
			       dark:border-gray-700 bg-white dark:bg-gray-900 shadow-xl overflow-hidden"
			role="listbox"
		>
			{#if $availableProviders.length === 0}
				<div class="flex items-start gap-3 p-4 text-sm text-gray-500 dark:text-gray-400">
					<AlertCircle class="h-4 w-4 text-amber-500 flex-shrink-0 mt-0.5" />
					<span>No AI providers are configured. Add an API key to your backend .env file.</span>
				</div>
			{:else}
				{#each $availableProviders as provider}
					<div class="px-3 pt-3 pb-1">
						<!-- Provider header -->
						<div class="flex items-center gap-2 px-2 py-1 mb-1">
							<span class="text-xs font-semibold uppercase tracking-wider text-gray-400
							            dark:text-gray-500">
								{provider.display_name}
							</span>
						</div>
						<!-- Models -->
						{#each provider.models as model}
							{@const isSelected = $selectedModel?.provider === provider.name && $selectedModel?.model === model.id}
							<button
								type="button"
								role="option"
								aria-selected={isSelected}
								on:click={() => select(provider.name, model.id, provider.display_name, model.display_name)}
								class="w-full flex items-start gap-3 rounded-xl px-3 py-2.5 text-left
								       transition-colors hover:bg-gray-50 dark:hover:bg-gray-800
								       {isSelected ? 'bg-brand-50 dark:bg-brand-950' : ''}"
							>
								<div class="flex-1 min-w-0">
									<p class="text-sm font-medium truncate
									          {isSelected
									            ? 'text-brand-700 dark:text-brand-300'
									            : 'text-gray-800 dark:text-gray-200'}">
										{model.display_name}
									</p>
									{#if model.description}
										<p class="text-xs text-gray-400 dark:text-gray-500 truncate mt-0.5">
											{model.description}
										</p>
									{/if}
								</div>
								{#if isSelected}
									<div class="mt-1 h-2 w-2 rounded-full bg-brand-500 flex-shrink-0"></div>
								{/if}
							</button>
						{/each}
					</div>
					<div class="mx-3 my-1 border-t border-gray-100 dark:border-gray-800 last:hidden"></div>
				{/each}
				<div class="px-3 pb-3"></div>
			{/if}
		</div>
	{/if}
</div>
