import { writable } from 'svelte/store';
import type { DashboardTimingRecord } from './timingDiagnostics.mjs';

export const dashboardTiming = writable<DashboardTimingRecord | null>(null);

export function clearDashboardTiming(): void {
	dashboardTiming.set(null);
}
