const API_URL = "http://localhost:8000/api";

export interface Job {
    title: string;
    company: string;
    location: string;
    description: string;
    link: string;
    source: string;
    score: number;
}

export interface RecommendationResponse{
    jobs: Job[];
    message?: string;
}

export async function getRecommendations(cvText: string, skills: string[]): Promise<RecommendationResponse> {
    const res = await fetch(`${API_URL}/jobs/recommend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cv_text: cvText, skills: skills})
    });

    if (!res.ok){
        throw new Error(`API Error: ${res.statusText}`);
    }
    return await res.json()
}