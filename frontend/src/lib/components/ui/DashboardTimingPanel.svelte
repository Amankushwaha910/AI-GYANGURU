<script lang="ts">
	import { dashboardTiming } from '$lib/api/dashboardTimingStore';
</script>

{#if $dashboardTiming}
	<aside
		class="mb-5 rounded-lg border border-sky-200 bg-sky-50 px-4 py-3 text-xs text-slate-700 dark:border-sky-900 dark:bg-sky-950/40 dark:text-slate-200"
		aria-label="Development dashboard request timing"
	>
		<div class="mb-2 flex items-center justify-between gap-3">
			<strong class="font-semibold">Development request timing</strong>
			<span
				class:font-semibold={$dashboardTiming.outcome !== 'success'}
				class:text-red-700={$dashboardTiming.outcome !== 'success'}
				class:text-green-700={$dashboardTiming.outcome === 'success'}
				role={$dashboardTiming.outcome === 'success' ? 'status' : 'alert'}
			>
				{$dashboardTiming.outcome === 'success' ? 'HTTP success' : $dashboardTiming.error}
			</span>
		</div>

		<dl class="grid grid-cols-2 gap-x-4 gap-y-1 sm:grid-cols-3">
			<div><dt class="inline font-medium">Request:</dt> <dd class="inline">{$dashboardTiming.method} {$dashboardTiming.route}</dd></div>
			<div><dt class="inline font-medium">HTTP status:</dt> <dd class="inline">{$dashboardTiming.status ?? 'No response'}</dd></div>
			<div><dt class="inline font-medium">Client total:</dt> <dd class="inline">{$dashboardTiming.totalMs.toFixed(1)} ms</dd></div>
			<div><dt class="inline font-medium">To response headers:</dt> <dd class="inline">{$dashboardTiming.headersMs === null ? 'Not available' : `${$dashboardTiming.headersMs.toFixed(1)} ms`}</dd></div>
			<div><dt class="inline font-medium">Body read/parse:</dt> <dd class="inline">{$dashboardTiming.bodyMs === null ? 'Not available' : `${$dashboardTiming.bodyMs.toFixed(1)} ms`}</dd></div>
			<div><dt class="inline font-medium">X-Request-ID:</dt> <dd class="inline break-all">{$dashboardTiming.requestId ?? 'Not provided'}</dd></div>
		</dl>

		<p class="mt-2 break-words"><strong class="font-medium">Server-Timing:</strong> {$dashboardTiming.serverTiming ?? 'Not provided'}</p>
	</aside>
{/if}
