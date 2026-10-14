/** @type {Promise<string | null> | null} */
let inFlightRefresh = null;

/**
 * Share one rotating refresh-token request among concurrent 401 responses.
 * @param {() => Promise<string | null>} refresh
 * @returns {Promise<string | null>}
 */
export function runRefreshSingleFlight(refresh) {
	if (!inFlightRefresh) {
		inFlightRefresh = Promise.resolve()
			.then(refresh)
			.finally(() => {
				inFlightRefresh = null;
			});
	}
	return inFlightRefresh;
}
