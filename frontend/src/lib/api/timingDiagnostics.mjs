const DASHBOARD_ROUTE = '/dashboard';

export function isDashboardTimingRequest(method, path) {
	return method.toUpperCase() === 'GET' && path.split('?')[0] === DASHBOARD_ROUTE;
}

export function createDashboardTimingRecord({
	method = 'GET',
	status = null,
	totalMs,
	headersMs = null,
	bodyMs = null,
	requestId = null,
	serverTiming = null,
	failureKind = null,
	errorName = null
}) {
	const outcome = failureKind === 'network'
		? 'network_error'
		: status === null
			? 'network_error'
			: status < 200 || status >= 300
				? 'http_error'
				: failureKind === 'body_parse'
					? 'body_parse_error'
					: 'success';

	const error = outcome === 'network_error'
		? `No HTTP response${errorName ? ` (${errorName})` : ''}`
		: outcome === 'http_error'
			? failureKind === 'authentication'
				? 'Authentication refresh failed'
				: `HTTP ${status}`
			: outcome === 'body_parse_error'
				? 'HTTP response body could not be parsed'
				: null;

	return {
		method,
		route: DASHBOARD_ROUTE,
		status,
		totalMs: roundMs(totalMs),
		headersMs: roundOptionalMs(headersMs),
		bodyMs: roundOptionalMs(bodyMs),
		requestId: requestId || null,
		serverTiming: serverTiming || null,
		outcome,
		error
	};
}

function roundMs(value) {
	return Number(value.toFixed(1));
}

function roundOptionalMs(value) {
	return value === null ? null : roundMs(value);
}
