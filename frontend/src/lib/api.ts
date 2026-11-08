import { authFetch } from './auth';

export const API_BASE =
	import.meta.env.VITE_BASE_URL ?? import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
const API_URL = `${API_BASE}/api`;

export interface Job {
	id?: number;
	title: string;
	company: string;
	location: string;
	other_locations?: string[];
	other_locations_total?: number;
	description: string;
	link: string;
	source: string;
	match_score: number;
	remote?: boolean;
	posted_at?: string | null;
	matched_skills?: string[];
	missing_skills?: string[];
	score_breakdown?: Partial<Record<'title' | 'skills' | 'semantic' | 'keywords', number>>;
}

export interface RecommendationResponse {
	jobs: Job[];
	message?: string;
	stats?: {
		pool_size: number;
		candidates: number;
		semantic: boolean;
		skills: boolean;
	};
}

export async function getRecommendations(
	cvText: string,
	query: string,
	skills: string[],
	seniority: string = 'All',
	country: string = "pl"
): Promise<RecommendationResponse> {
	const res = await authFetch(`${API_URL}/jobs/recommend`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ cv_text: cvText, query: query, skills: skills, seniority: seniority, country:country})
	});

	if (!res.ok) {
		const data = await res.json().catch(() => ({}));
		throw new Error(
			typeof data.detail === 'string' ? data.detail : `Job search failed (${res.status}).`
		);
	}
	return await res.json();
}

export async function getATSScore(cvText: string, jobDescription: string):
Promise<{
	score: number;
	missing_keywords: string[];
	formatting_issues: string[];
	suggestions: string[];
}> {
	const res = await authFetch(`${API_BASE}/api/ats_score`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json'},
		body: JSON.stringify({ cv_text: cvText, job_description: jobDescription})

	});
	if (!res.ok) {
		const data = await res.json().catch(() => ({}));
		throw new Error(data.detail || 'Failed to get ATS score');
	}
	return await res.json();
}
