import { writable, get } from 'svelte/store';
import { goto } from '$app/navigation';
import { API_BASE } from './api';
import { browser } from '$app/environment';

function getStoredToken() {
    if (!browser) return null;

    const sessionToken = sessionStorage.getItem('token');
    if (sessionToken) {
        localStorage.removeItem('token');
        return sessionToken;
    }

    const legacyToken = localStorage.getItem('token');
    if (legacyToken) {
        sessionStorage.setItem('token', legacyToken);
        localStorage.removeItem('token');
        return legacyToken;
    }

    return null;
}

const initialToken = getStoredToken();
export const userToken = writable<string | null>(initialToken);

export function setToken(token: string) {
    if (browser) {
        sessionStorage.setItem('token', token);
        localStorage.removeItem('token');
    }
    userToken.set(token);
}

export function clearToken() {
    if (browser) {
        sessionStorage.removeItem('token');
        localStorage.removeItem('token');
    }
    userToken.set(null);
}

export async function logout() {
    const token = get(userToken);
    if (token) {
        try {
            await fetch(`${API_BASE}/auth/logout`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
        } catch (e) {
            console.error("Logout failed", e);
        }
    }
    clearToken();
    goto('/login');
}

export async function authFetch(url: string, options: RequestInit = {}) {
    const token = get(userToken);
    const headers = new Headers(options.headers || {});

    if (token) {
        headers.set('Authorization', `Bearer ${token}`);
    }

    const res = await fetch(url, { ...options, headers });

    if (res.status === 401) {
        clearToken();
        goto('/login');
        throw new Error("Unauthorized");
    }

    return res;
}
