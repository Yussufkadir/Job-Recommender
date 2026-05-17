import { authFetch } from './auth';

export const API_BASE =
	import.meta.env.VITE_BASE_URL ?? import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
const API_URL = `${API_BASE}/api`;

export interface Job {
	title: string;
	company: string;
	location: string;
	description: string;
	link: string;
	source: string;
	match_score: number;
}

export interface RecommendationResponse {
	jobs: Job[];
	message?: string;
}

export async function getRecommendations(
	cvText: string,
	query: string,
	skills: string[],
	seniority: string = 'All'
): Promise<RecommendationResponse> {
	const res = await authFetch(`${API_URL}/jobs/recommend`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ cv_text: cvText, query: query, skills: skills, seniority: seniority })
	});

	if (!res.ok) {
		throw new Error(`API Error: ${res.statusText}`);
	}
	return await res.json();
}
