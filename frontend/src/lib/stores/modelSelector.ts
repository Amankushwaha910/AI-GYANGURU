/**
 * AI model selection store.
 * Persists the user's chosen provider+model across all modules (summary, explanation, quiz).
 * Preference is saved to localStorage so it survives page refreshes.
 */
import { browser } from '$app/environment';
import { writable, derived, get } from 'svelte/store';
import type { SelectedModel, AIModelsResponse, AIProviderInfo } from '$types';

const STORAGE_KEY = 'gyanguru_selected_model';

function loadFromStorage(): SelectedModel | null {
	if (!browser) return null;
	try {
		const raw = localStorage.getItem(STORAGE_KEY);
		return raw ? JSON.parse(raw) : null;
	} catch {
		return null;
	}
}

function saveToStorage(model: SelectedModel) {
	if (browser) {
		localStorage.setItem(STORAGE_KEY, JSON.stringify(model));
	}
}

interface ModelSelectorState {
	selected: SelectedModel | null;
	providers: AIProviderInfo[];
	loading: boolean;
	error: string;
}

function createModelSelectorStore() {
	const stored = loadFromStorage();
	const { subscribe, set, update } = writable<ModelSelectorState>({
		selected: stored,
		providers: [],
		loading: false,
		error: '',
	});

	return {
		subscribe,

		/** Load available models from the backend /models endpoint. */
		async load(modelsApi: { list: () => Promise<any> }) {
			update((s) => ({ ...s, loading: true, error: '' }));
			try {
				const res = await modelsApi.list();
				const data: AIModelsResponse = res.data;

				update((s) => {
					// If no model is selected yet, pick the backend default
					let selected = s.selected;
					if (!selected && data.providers.length > 0) {
						const defaultProvider = data.providers.find(
							(p) => p.name === data.default_provider
						);
						if (defaultProvider) {
							const defaultModel = defaultProvider.models.find(
								(m) => m.id === data.default_model
							) ?? defaultProvider.models[0];
							if (defaultModel) {
								selected = {
									provider: defaultProvider.name,
									model: defaultModel.id,
									display: `${defaultProvider.display_name} — ${defaultModel.display_name}`,
								};
								saveToStorage(selected);
							}
						}
					}
					return { ...s, providers: data.providers, selected, loading: false };
				});
			} catch (e: any) {
				update((s) => ({
					...s,
					loading: false,
					error: e?.message ?? 'Failed to load AI models',
				}));
			}
		},

		/** Select a specific provider+model. */
		select(provider: string, modelId: string, display: string) {
			const selected: SelectedModel = { provider, model: modelId, display };
			saveToStorage(selected);
			update((s) => ({ ...s, selected }));
		},

		/** Get the current selection as { provider, model } for API requests. */
		getSelection(): { provider: string | undefined; model: string | undefined } {
			const state = get({ subscribe });
			return {
				provider: state.selected?.provider,
				model: state.selected?.model,
			};
		},
	};
}

export const modelSelector = createModelSelectorStore();

// Derived helpers
export const selectedModel = derived(modelSelector, ($s) => $s.selected);
export const availableProviders = derived(modelSelector, ($s) => $s.providers);
export const modelsLoading = derived(modelSelector, ($s) => $s.loading);
