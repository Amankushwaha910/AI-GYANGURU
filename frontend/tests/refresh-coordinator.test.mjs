import test from 'node:test';
import assert from 'node:assert/strict';
import { runRefreshSingleFlight } from '../src/lib/api/refreshCoordinator.mjs';

test('concurrent unauthorized requests share one token rotation', async () => {
	let release;
	const gate = new Promise((resolve) => (release = resolve));
	let calls = 0;
	const refresh = async () => {
		calls += 1;
		await gate;
		return 'new-access-token';
	};

	const first = runRefreshSingleFlight(refresh);
	const second = runRefreshSingleFlight(refresh);
	assert.equal(calls, 0);
	release();
	const [firstToken, secondToken] = await Promise.all([first, second]);

	assert.equal(calls, 1);
	assert.equal(firstToken, 'new-access-token');
	assert.equal(secondToken, 'new-access-token');
});

test('a later refresh can retry after a prior failed refresh', async () => {
	await assert.rejects(
		runRefreshSingleFlight(async () => {
			throw new Error('temporary failure');
		}),
		/temporary failure/
	);

	assert.equal(
		await runRefreshSingleFlight(async () => 'recovered-token'),
		'recovered-token'
	);
});
