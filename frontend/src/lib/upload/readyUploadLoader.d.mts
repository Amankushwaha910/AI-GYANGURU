export function createReadyUploadLoader<T extends { status: string }>(
	fetchUploads: () => Promise<{ data: T[] }>
): { load: () => Promise<T[]>; invalidate: () => void };
