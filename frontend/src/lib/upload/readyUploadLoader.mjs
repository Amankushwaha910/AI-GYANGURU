/** Cache a completed-file list after its first successful load and coalesce concurrent loads. */
/** @template {{ status: string }} T @param {() => Promise<{ data: T[] }>} fetchUploads @returns {{ load: () => Promise<T[]>, invalidate: () => void }} */
export function createReadyUploadLoader(fetchUploads) {
	/** @type {T[] | null} */
	let cached = null;
	/** @type {Promise<T[]> | null} */
	let pending = null;

	return {
		load() {
			if (cached) return Promise.resolve(cached);
			if (!pending) {
				pending = Promise.resolve()
					.then(fetchUploads)
					.then((response) => {
						cached = response.data.filter((upload) => upload.status === 'completed');
						return cached;
					})
					.finally(() => { pending = null; });
			}
			return pending;
		},
		invalidate() {
			cached = null;
		},
	};
}
