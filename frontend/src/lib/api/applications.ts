import { authFetch } from '../auth';
import { API_BASE } from '../api';
import type { Application, ApplicationStatus } from '../types/application';

const API_URL = `${API_BASE}/api/applications`;

export async function getApplications(): Promise<Application[]> {
    const res = await authFetch(API_URL);
    if (!res.ok) {
        throw new Error(`API Error: ${res.statusText}`);
    }
    return await res.json();
}

export async function updateApplicationStatus(id: number, status: ApplicationStatus): Promise<Application> {
    const res = await authFetch(`${API_URL}/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status })
    });
    if (!res.ok) {
        throw new Error(`API Error: ${res.statusText}`);
    }
    return await res.json();
}
