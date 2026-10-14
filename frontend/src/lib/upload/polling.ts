export type PollBatchResult<T> = {
	id: string;
	result: PromiseSettledResult<T>;
};

export type PollRequest<T> = (id: string, signal: AbortSignal) => Promise<T>;

export const MAX_CONSECUTIVE_POLL_FAILURES = 3;

/** Serialize polling batches and let a page cancel status requests on teardown. */
export function createPollBatchRunner() {
	let running = false;
	let destroyed = false;
	const controllers = new Map<string, AbortController>();

	return {
		async run<T>(ids: string[], request: PollRequest<T>): Promise<PollBatchResult<T>[] | null> {
			if (running || destroyed) return null;
			running = true;

			const entries = [...new Set(ids)]
				.filter((id) => !controllers.has(id))
				.map((id) => {
					const controller = new AbortController();
					controllers.set(id, controller);
					return { id, controller };
				});

			try {
				const settled = await Promise.allSettled(
					entries.map(({ id, controller }) =>
						Promise.resolve().then(() => request(id, controller.signal))
					)
				);
				if (destroyed) return null;
				return entries.map(({ id }, index) => ({ id, result: settled[index] }));
			} finally {
				for (const { id, controller } of entries) {
					if (controllers.get(id) === controller) controllers.delete(id);
				}
				if (!destroyed) running = false;
			}
		},

		abort(id: string) {
			controllers.get(id)?.abort();
		},

		destroy() {
			if (destroyed) return;
			destroyed = true;
			for (const controller of controllers.values()) controller.abort();
		}
	};
}

export function isUploadInProgress(status: string): boolean {
	return status === 'pending' || status === 'processing';
}

export function stopPollingForStatus(id: string, status: string, pollingIds: Set<string>): boolean {
	if (isUploadInProgress(status)) return false;
	pollingIds.delete(id);
	return true;
}

export function classifyPollFailure(
	error: unknown,
	consecutiveFailures: number
): { stop: boolean; message: string } {
	const status =
		typeof error === 'object' && error !== null && 'status' in error
			? Number((error as { status: unknown }).status)
			: NaN;

	if (status === 401) {
		return { stop: true, message: 'Session could not be verified. Status polling stopped; please sign in again.' };
	}
	if (status === 403) {
		return { stop: true, message: 'Access denied while checking this file. Status polling stopped.' };
	}
	if (status >= 400 && status < 500 && status !== 408 && status !== 429) {
		return { stop: true, message: `Status check failed (HTTP ${status}). Polling stopped.` };
	}

	if (consecutiveFailures >= MAX_CONSECUTIVE_POLL_FAILURES) {
		return {
			stop: true,
			message: `Status check failed ${consecutiveFailures} times. Automatic polling stopped; retry when ready.`
		};
	}
	return {
		stop: false,
		message: `Temporary status check failure. Retrying (${consecutiveFailures}/${MAX_CONSECUTIVE_POLL_FAILURES})…`
	};
}

export function applyPollFailure(
	id: string,
	error: unknown,
	failureCounts: Map<string, number>,
	pollingIds: Set<string>
): { stop: boolean; message: string; consecutiveFailures: number } {
	const consecutiveFailures = (failureCounts.get(id) ?? 0) + 1;
	failureCounts.set(id, consecutiveFailures);
	const failure = classifyPollFailure(error, consecutiveFailures);
	if (failure.stop) pollingIds.delete(id);
	return { ...failure, consecutiveFailures };
}
