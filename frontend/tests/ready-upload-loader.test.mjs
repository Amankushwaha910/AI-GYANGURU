import test from 'node:test';
import assert from 'node:assert/strict';
import { createReadyUploadLoader } from '../src/lib/upload/readyUploadLoader.mjs';

test('does not fetch until requested, then caches completed uploads', async () => {
	let calls = 0;
	const loader = createReadyUploadLoader(async () => {
		calls += 1;
		return { data: [{ id: 'ready', status: 'completed' }, { id: 'pending', status: 'processing' }] };
	});
	assert.equal(calls, 0);
	assert.deepEqual(await loader.load(), [{ id: 'ready', status: 'completed' }]);
	assert.deepEqual(await loader.load(), [{ id: 'ready', status: 'completed' }]);
	assert.equal(calls, 1);
});

test('coalesces concurrent loads and allows retry after a failed request', async () => {
	let calls = 0;
	const loader = createReadyUploadLoader(async () => {
		calls += 1;
		if (calls === 1) throw new Error('temporary');
		return { data: [{ id: 'ready', status: 'completed' }] };
	});
	await assert.rejects(loader.load(), /temporary/);
	const [first, second] = await Promise.all([loader.load(), loader.load()]);
	assert.deepEqual(first, second);
	assert.equal(calls, 2);
});

test('invalidate refreshes the completed-file cache', async () => {
	let calls = 0;
	const loader = createReadyUploadLoader(async () => ({ data: [{ id: String(++calls), status: 'completed' }] }));
	assert.equal((await loader.load())[0].id, '1');
	loader.invalidate();
	assert.equal((await loader.load())[0].id, '2');
});
