import assert from 'node:assert/strict';
import test from 'node:test';
import {
	applyPollFailure,
	createPollBatchRunner,
	isUploadInProgress,
	MAX_CONSECUTIVE_POLL_FAILURES,
	stopPollingForStatus
} from '../src/lib/upload/polling.ts';

function deferred() {
	let resolve;
	const promise = new Promise((done) => {
		resolve = done;
	});
	return { promise, resolve };
}

test('slow poll batches do not overlap and duplicate IDs run once', async () => {
	const runner = createPollBatchRunner();
	const pending = deferred();
	let active = 0;
	let maxActive = 0;
	let calls = 0;

	const firstBatch = runner.run(['file-a', 'file-a'], async () => {
		calls += 1;
		active += 1;
		maxActive = Math.max(maxActive, active);
		const value = await pending.promise;
		active -= 1;
		return value;
	});

	await Promise.resolve();
	const overlappingBatch = await runner.run(['file-a'], async () => {
		calls += 1;
		return 'unexpected';
	});
	assert.equal(overlappingBatch, null);
	assert.equal(calls, 1);

	pending.resolve('processing');
	assert.deepEqual(await firstBatch, [
		{ id: 'file-a', result: { status: 'fulfilled', value: 'processing' } }
	]);
	assert.equal(maxActive, 1);

	const nextBatch = await runner.run(['file-a'], async () => {
		calls += 1;
		return 'completed';
	});
	assert.equal(nextBatch[0].result.status, 'fulfilled');
	assert.equal(calls, 2);
});

test('destroy aborts in-flight polls and suppresses their results', async () => {
	const runner = createPollBatchRunner();
	let observedSignal;
	const pendingBatch = runner.run(['file-a'], (_id, signal) => new Promise((resolve) => {
		observedSignal = signal;
		signal.addEventListener('abort', () => resolve('late result'), { once: true });
	}));

	await Promise.resolve();
	runner.destroy();
	assert.equal(observedSignal.aborted, true);
	assert.equal(await pendingBatch, null);
	assert.equal(await runner.run(['file-a'], async () => 'unexpected'), null);
});

test('authorization failures stop polling immediately', () => {
	for (const status of [401, 403]) {
		const id = String(status);
		const pollingIds = new Set([id]);
		const failure = applyPollFailure(id, { status }, new Map(), pollingIds);
		assert.equal(failure.stop, true);
		assert.equal(pollingIds.has(id), false);
		assert.match(failure.message, status === 401 ? /sign in/i : /access denied/i);
	}
});

test('transient failures retry only up to the configured limit', () => {
	const pollingIds = new Set(['file-a']);
	const failureCounts = new Map();
	assert.equal(applyPollFailure('file-a', new TypeError('network'), failureCounts, pollingIds).stop, false);
	assert.equal(applyPollFailure('file-a', { status: 503 }, failureCounts, pollingIds).stop, false);
	const exhausted = applyPollFailure('file-a', new TypeError('network'), failureCounts, pollingIds);
	assert.equal(exhausted.stop, true);
	assert.equal(pollingIds.has('file-a'), false);
	assert.match(exhausted.message, /automatic polling stopped/i);
});

test('processing statuses continue while completed and failed statuses are terminal', () => {
	assert.equal(isUploadInProgress('pending'), true);
	assert.equal(isUploadInProgress('processing'), true);
	assert.equal(isUploadInProgress('completed'), false);
	assert.equal(isUploadInProgress('failed'), false);
	const pollingIds = new Set(['processing', 'completed']);
	assert.equal(stopPollingForStatus('processing', 'processing', pollingIds), false);
	assert.equal(stopPollingForStatus('completed', 'completed', pollingIds), true);
	assert.deepEqual([...pollingIds], ['processing']);
});
