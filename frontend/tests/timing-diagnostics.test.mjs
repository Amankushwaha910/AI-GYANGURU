import assert from 'node:assert/strict';
import test from 'node:test';

import {
	createDashboardTimingRecord,
	isDashboardTimingRequest
} from '../src/lib/api/timingDiagnostics.mjs';

test('captures only the dashboard GET route, ignoring query parameters', () => {
	assert.equal(isDashboardTimingRequest('GET', '/dashboard?refresh=1'), true);
	assert.equal(isDashboardTimingRequest('POST', '/dashboard'), false);
	assert.equal(isDashboardTimingRequest('GET', '/analytics/dashboard'), false);
});

test('reports HTTP status and client timings with response correlation headers', () => {
	const record = createDashboardTimingRecord({
		method: 'GET',
		status: 200,
		totalMs: 123.456,
		headersMs: 120.04,
		bodyMs: 3.416,
		requestId: 'req-123',
		serverTiming: 'app;dur=98.2'
	});

	assert.deepEqual(record, {
		method: 'GET',
		route: '/dashboard',
		status: 200,
		totalMs: 123.5,
		headersMs: 120,
		bodyMs: 3.4,
		requestId: 'req-123',
		serverTiming: 'app;dur=98.2',
		outcome: 'success',
		error: null
	});
});

test('does not label an HTTP or body-parse failure as successful', () => {
	const httpError = createDashboardTimingRecord({ status: 503, totalMs: 50 });
	const parseError = createDashboardTimingRecord({
		status: 200,
		totalMs: 50,
		failureKind: 'body_parse'
	});

	assert.equal(httpError.outcome, 'http_error');
	assert.equal(httpError.error, 'HTTP 503');
	assert.equal(parseError.outcome, 'body_parse_error');
	assert.equal(parseError.error, 'HTTP response body could not be parsed');
});

test('reports network failure without inventing a status or response headers', () => {
	const record = createDashboardTimingRecord({
		status: null,
		totalMs: 22.25,
		failureKind: 'network',
		errorName: 'TypeError'
	});

	assert.equal(record.outcome, 'network_error');
	assert.equal(record.status, null);
	assert.equal(record.error, 'No HTTP response (TypeError)');
	assert.equal(record.requestId, null);
	assert.equal(record.serverTiming, null);
});
