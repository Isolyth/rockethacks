import type { UserResponse } from '$lib/types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface AuthState {
	token: string | null;
	user: UserResponse | null;
	encryptionKey: string | null;
	loading: boolean;
}

export const auth: AuthState = $state({
	token: null,
	user: null,
	encryptionKey: null,
	loading: true
});

export function setAuth(token: string, user: UserResponse, encryptionKey?: string | null) {
	auth.token = token;
	auth.user = user;
	auth.encryptionKey = encryptionKey ?? null;
	auth.loading = false;
	localStorage.setItem('auth_token', token);
	if (encryptionKey) {
		sessionStorage.setItem('enc_key', encryptionKey);
	}
}

export function clearAuth() {
	auth.token = null;
	auth.user = null;
	auth.encryptionKey = null;
	auth.loading = false;
	localStorage.removeItem('auth_token');
	sessionStorage.removeItem('enc_key');
}

export function isAuthenticated(): boolean {
	return auth.token !== null && auth.user !== null;
}

export async function hydrateAuth() {
	const saved = localStorage.getItem('auth_token');
	if (!saved) {
		auth.loading = false;
		return;
	}

	try {
		const resp = await fetch(`${API_URL}/auth/me`, {
			headers: { Authorization: `Bearer ${saved}` }
		});
		if (resp.ok) {
			const user: UserResponse = await resp.json();
			auth.token = saved;
			auth.user = user;
			// Restore encryption key from sessionStorage (survives page refresh within same tab)
			auth.encryptionKey = sessionStorage.getItem('enc_key');
		} else {
			localStorage.removeItem('auth_token');
			sessionStorage.removeItem('enc_key');
		}
	} catch {
		localStorage.removeItem('auth_token');
		sessionStorage.removeItem('enc_key');
	}
	auth.loading = false;
}
