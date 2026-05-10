import { browser } from '$app/environment';
import { writable } from 'svelte/store';

export interface CvWorkspaceState {
	cvText: string;
	fileName: string;
	fullName: string;
	sourceName: string;
	extractedText: string;
	skills: string[];
}

const STORAGE_KEY = 'shared-cv-workspace';
const LEGACY_STORAGE_KEYS = {
	cvText: 'cv-builder-draft',
	fileName: 'cv-builder-file-name',
	fullName: 'cv-builder-full-name'
} as const;

const defaultCvWorkspaceState: CvWorkspaceState = {
	cvText: '',
	fileName: 'my_cv',
	fullName: '',
	sourceName: '',
	extractedText: '',
	skills: []
};

let storageListenerAttached = false;

function normalizeSkills(skills: string[] | undefined) {
	const normalized: string[] = [];
	const seen = new Set<string>();

	for (const rawSkill of skills ?? []) {
		const skill = rawSkill.trim();
		if (!skill) {
			continue;
		}

		const key = skill.toLowerCase();
		if (seen.has(key)) {
			continue;
		}

		seen.add(key);
		normalized.push(skill);
	}

	return normalized;
}

function normalizeState(state?: Partial<CvWorkspaceState> | null): CvWorkspaceState {
	return {
		cvText: typeof state?.cvText === 'string' ? state.cvText : '',
		fileName:
			typeof state?.fileName === 'string' && state.fileName.trim()
				? state.fileName
				: defaultCvWorkspaceState.fileName,
		fullName: typeof state?.fullName === 'string' ? state.fullName : '',
		sourceName: typeof state?.sourceName === 'string' ? state.sourceName : '',
		extractedText: typeof state?.extractedText === 'string' ? state.extractedText : '',
		skills: normalizeSkills(
			Array.isArray(state?.skills)
				? state.skills.filter((skill): skill is string => typeof skill === 'string')
				: []
		)
	};
}

function arraysEqual(left: string[], right: string[]) {
	return left.length === right.length && left.every((value, index) => value === right[index]);
}

function statesEqual(left: CvWorkspaceState, right: CvWorkspaceState) {
	return (
		left.cvText === right.cvText &&
		left.fileName === right.fileName &&
		left.fullName === right.fullName &&
		left.sourceName === right.sourceName &&
		left.extractedText === right.extractedText &&
		arraysEqual(left.skills, right.skills)
	);
}

function clearLegacyStorage() {
	if (!browser) {
		return;
	}

	for (const key of Object.values(LEGACY_STORAGE_KEYS)) {
		localStorage.removeItem(key);
		sessionStorage.removeItem(key);
	}
}

function readLegacyValue(key: string) {
	if (!browser) {
		return null;
	}

	const sessionValue = sessionStorage.getItem(key);
	if (sessionValue !== null) {
		return sessionValue;
	}

	const localValue = localStorage.getItem(key);
	if (localValue !== null) {
		sessionStorage.setItem(key, localValue);
		localStorage.removeItem(key);
		return localValue;
	}

	return null;
}

function shouldPersistState(state: CvWorkspaceState) {
	return !statesEqual(state, defaultCvWorkspaceState);
}

function clearPersistedState() {
	if (!browser) {
		return;
	}

	sessionStorage.removeItem(STORAGE_KEY);
	localStorage.removeItem(STORAGE_KEY);
	clearLegacyStorage();
}

function persistState(state: CvWorkspaceState) {
	if (!browser) {
		return;
	}

	if (!shouldPersistState(state)) {
		clearPersistedState();
		return;
	}

	sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
	localStorage.removeItem(STORAGE_KEY);
	clearLegacyStorage();
}

function loadState() {
	if (!browser) {
		return defaultCvWorkspaceState;
	}

	const storedState = sessionStorage.getItem(STORAGE_KEY);
	if (storedState) {
		try {
			return normalizeState(JSON.parse(storedState) as Partial<CvWorkspaceState>);
		} catch (error) {
			console.error('Failed to parse the saved CV workspace state.', error);
			sessionStorage.removeItem(STORAGE_KEY);
		}
	}

	const legacyStoredState = localStorage.getItem(STORAGE_KEY);
	if (legacyStoredState) {
		try {
			const normalizedState = normalizeState(
				JSON.parse(legacyStoredState) as Partial<CvWorkspaceState>
			);
			persistState(normalizedState);
			return normalizedState;
		} catch (error) {
			console.error('Failed to parse the legacy CV workspace state.', error);
			localStorage.removeItem(STORAGE_KEY);
		}
	}

	const legacyState = normalizeState({
		cvText: readLegacyValue(LEGACY_STORAGE_KEYS.cvText) ?? '',
		fileName: readLegacyValue(LEGACY_STORAGE_KEYS.fileName) ?? defaultCvWorkspaceState.fileName,
		fullName: readLegacyValue(LEGACY_STORAGE_KEYS.fullName) ?? ''
	});

	const hasLegacyData =
		Boolean(legacyState.cvText.trim()) ||
		Boolean(legacyState.fullName.trim()) ||
		legacyState.fileName !== defaultCvWorkspaceState.fileName;

	clearLegacyStorage();

	if (hasLegacyData) {
		persistState(legacyState);
		return legacyState;
	}

	return defaultCvWorkspaceState;
}

function createCvWorkspaceStore() {
	const { subscribe, set, update } = writable<CvWorkspaceState>(loadState());

	if (browser && !storageListenerAttached) {
		window.addEventListener('storage', (event) => {
			if (!event.key || event.key === STORAGE_KEY) {
				set(loadState());
			}
		});
		storageListenerAttached = true;
	}

	return {
		subscribe,
		patch(patch: Partial<CvWorkspaceState>) {
			update((current) => {
				const next = normalizeState({ ...current, ...patch });

				if (statesEqual(current, next)) {
					return current;
				}

				persistState(next);
				return next;
			});
		},
		clear() {
			clearPersistedState();
			set(defaultCvWorkspaceState);
		}
	};
}

export const cvWorkspace = createCvWorkspaceStore();
