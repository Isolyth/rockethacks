import type {
	ProgressEvent,
	FinancialReport,
	PodcastAudio,
	DocumentRequest,
	AgentQuestion,
	AuthResponse,
	UserResponse,
	ReportSummaryItem,
	ReportDetail,
	StatementItem
} from './types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface AnalysisHandle {
	respond: (action: 'upload' | 'skip', files?: File[]) => Promise<void>;
	answerQuestion: (answer: string) => void;
	close: () => void;
}

async function fileToBase64(file: File): Promise<string> {
	const buffer = await file.arrayBuffer();
	const bytes = new Uint8Array(buffer);
	let binary = '';
	for (let i = 0; i < bytes.length; i++) {
		binary += String.fromCharCode(bytes[i]);
	}
	return btoa(binary);
}

async function filesToPayload(files: File[]): Promise<{ name: string; content: string }[]> {
	return Promise.all(
		files.map(async (f) => ({
			name: f.name,
			content: await fileToBase64(f)
		}))
	);
}

// --- REST API functions ---

async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
	return fetch(`${API_URL}${path}`, {
		...options,
		headers: {
			'Content-Type': 'application/json',
			...options.headers
		}
	});
}

function authHeaders(token: string): HeadersInit {
	return { Authorization: `Bearer ${token}` };
}

export async function signup(
	email: string,
	password: string,
	displayName?: string
): Promise<AuthResponse> {
	const resp = await apiFetch('/auth/signup', {
		method: 'POST',
		body: JSON.stringify({ email, password, display_name: displayName || undefined })
	});
	if (!resp.ok) {
		const err = await resp.json().catch(() => ({ detail: 'Signup failed' }));
		throw new Error(err.detail || 'Signup failed');
	}
	return resp.json();
}

export async function login(email: string, password: string): Promise<AuthResponse> {
	const resp = await apiFetch('/auth/login', {
		method: 'POST',
		body: JSON.stringify({ email, password })
	});
	if (!resp.ok) {
		const err = await resp.json().catch(() => ({ detail: 'Login failed' }));
		throw new Error(err.detail || 'Login failed');
	}
	return resp.json();
}

export async function fetchReports(token: string): Promise<ReportSummaryItem[]> {
	const resp = await apiFetch('/dashboard/reports', { headers: authHeaders(token) });
	if (!resp.ok) throw new Error('Failed to fetch reports');
	return resp.json();
}

export async function fetchReport(token: string, reportId: string): Promise<ReportDetail> {
	const resp = await apiFetch(`/dashboard/reports/${reportId}`, {
		headers: authHeaders(token)
	});
	if (!resp.ok) throw new Error('Failed to fetch report');
	return resp.json();
}

export async function fetchStatements(token: string): Promise<StatementItem[]> {
	const resp = await apiFetch('/dashboard/statements', { headers: authHeaders(token) });
	if (!resp.ok) throw new Error('Failed to fetch statements');
	return resp.json();
}

export async function deleteReport(token: string, reportId: string): Promise<void> {
	const resp = await apiFetch(`/dashboard/reports/${reportId}`, {
		method: 'DELETE',
		headers: authHeaders(token)
	});
	if (!resp.ok) throw new Error('Failed to delete report');
}

export async function deleteStatement(token: string, statementId: string): Promise<void> {
	const resp = await apiFetch(`/dashboard/statements/${statementId}`, {
		method: 'DELETE',
		headers: authHeaders(token)
	});
	if (!resp.ok) throw new Error('Failed to delete statement');
}

// --- WebSocket analysis ---

interface AnalysisOptions {
	files: File[];
	language: string;
	token?: string | null;
	encryptionKey?: string | null;
	savedStatementIds?: string[];
	onProgress: (event: ProgressEvent) => void;
	onReportReady: (report: FinancialReport) => void;
	onPodcastAudioReady: (audio: PodcastAudio & { report_id?: string }) => void;
	onError: (message: string) => void;
	onDocumentRequest: (request: DocumentRequest) => void;
	onAskQuestion: (question: AgentQuestion) => void;
	onThinking: (text: string) => void;
}

export function startAnalysis(opts: AnalysisOptions): AnalysisHandle {
	const baseUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/analyze';
	let wsUrl = baseUrl;
	if (opts.token) {
		wsUrl += `?token=${opts.token}`;
		if (opts.encryptionKey) {
			wsUrl += `&enc_key=${encodeURIComponent(opts.encryptionKey)}`;
		}
	}
	const ws = new WebSocket(wsUrl);
	let open = false;

	ws.onopen = async () => {
		open = true;
		try {
			if (opts.savedStatementIds && opts.savedStatementIds.length > 0) {
				// Use saved statements flow
				const newFiles =
					opts.files.length > 0 ? await filesToPayload(opts.files) : undefined;
				ws.send(
					JSON.stringify({
						type: 'use_saved_statements',
						statement_ids: opts.savedStatementIds,
						files: newFiles,
						language: opts.language
					})
				);
			} else {
				const payload = await filesToPayload(opts.files);
				ws.send(
					JSON.stringify({
						type: 'upload_files',
						files: payload,
						language: opts.language
					})
				);
			}
		} catch {
			opts.onError('Failed to read files');
		}
	};

	ws.onmessage = (event) => {
		try {
			const data = JSON.parse(event.data);
			switch (data.type) {
				case 'progress':
					opts.onProgress(data);
					break;
				case 'thinking':
					opts.onThinking(data.text);
					break;
				case 'request_documents':
					opts.onDocumentRequest(data);
					break;
				case 'ask_question':
					opts.onAskQuestion(data);
					break;
				case 'report_ready':
					opts.onReportReady(data.report);
					break;
				case 'podcast_audio_ready':
					opts.onPodcastAudioReady(data);
					break;
				case 'error':
					opts.onError(data.message);
					break;
			}
		} catch (e) {
			console.warn('Malformed WebSocket message:', e);
		}
	};

	ws.onerror = () => {
		opts.onError('WebSocket connection error. Is the backend running?');
	};

	ws.onclose = () => {
		open = false;
	};

	return {
		async respond(action: 'upload' | 'skip', responseFiles?: File[]) {
			if (!open) return;
			if (action === 'upload' && responseFiles?.length) {
				const payload = await filesToPayload(responseFiles);
				ws.send(JSON.stringify({ type: 'upload_files', files: payload }));
			} else {
				ws.send(JSON.stringify({ type: 'skip' }));
			}
		},
		answerQuestion(answer: string) {
			if (!open) return;
			ws.send(JSON.stringify({ type: 'answer_question', answer }));
		},
		close() {
			if (open) ws.close();
		}
	};
}
