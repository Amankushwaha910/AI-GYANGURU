export type DashboardTimingOutcome =
	| 'success'
	| 'http_error'
	| 'network_error'
	| 'body_parse_error';

export interface DashboardTimingRecord {
	method: string;
	route: '/dashboard';
	status: number | null;
	totalMs: number;
	headersMs: number | null;
	bodyMs: number | null;
	requestId: string | null;
	serverTiming: string | null;
	outcome: DashboardTimingOutcome;
	error: string | null;
}

export function isDashboardTimingRequest(method: string, path: string): boolean;

export function createDashboardTimingRecord(input: {
	method?: string;
	status?: number | null;
	totalMs: number;
	headersMs?: number | null;
	bodyMs?: number | null;
	requestId?: string | null;
	serverTiming?: string | null;
	failureKind?: 'network' | 'body_parse' | 'authentication' | null;
	errorName?: string | null;
}): DashboardTimingRecord;
