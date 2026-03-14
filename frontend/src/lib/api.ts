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
	const resp = await apiFetch(`/dashboard/reports/${encodeURIComponent(reportId)}`, {
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
	const resp = await apiFetch(`/dashboard/reports/${encodeURIComponent(reportId)}`, {
		method: 'DELETE',
		headers: authHeaders(token)
	});
	if (!resp.ok) throw new Error('Failed to delete report');
}

export async function deleteStatement(token: string, statementId: string): Promise<void> {
	const resp = await apiFetch(`/dashboard/statements/${encodeURIComponent(statementId)}`, {
		method: 'DELETE',
		headers: authHeaders(token)
	});
	if (!resp.ok) throw new Error('Failed to delete statement');
}

export async function streamFollowup(
	token: string | null,
	reportData: FinancialReport,
	prompt: string,
	history: { role: string; content: string }[] = [],
	language: string = 'en',
	callbacks: {
		onChunk: (text: string) => void;
		onDone: (fullText: string, podcastScript?: string) => void;
		onError: (message: string) => void;
	}
): Promise<void> {
	const hdrs: Record<string, string> = { 'Content-Type': 'application/json' };
	if (token) hdrs['Authorization'] = `Bearer ${token}`;

	const resp = await fetch(`${API_URL}/analyze/follow-up`, {
		method: 'POST',
		headers: hdrs,
		body: JSON.stringify({ report_data: reportData, prompt, history, language })
	});

	if (!resp.ok) {
		const err = await resp.json().catch(() => ({ detail: 'Request failed' }));
		callbacks.onError(err.detail || 'Request failed');
		return;
	}

	const reader = resp.body!.getReader();
	const decoder = new TextDecoder();
	let buffer = '';

	while (true) {
		const { done, value } = await reader.read();
		if (done) break;
		buffer += decoder.decode(value, { stream: true });

		const parts = buffer.split('\n\n');
		buffer = parts.pop()!;

		for (const part of parts) {
			if (!part.startsWith('data: ')) continue;
			try {
				const data = JSON.parse(part.slice(6));
				if (data.type === 'chunk') callbacks.onChunk(data.text);
				else if (data.type === 'done') callbacks.onDone(data.full_text, data.podcast_script);
				else if (data.type === 'error') callbacks.onError(data.message);
			} catch {
				// skip malformed SSE
			}
		}
	}
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
	// Auto-detect protocol: use wss/https in production, ws/http locally
	const wsProtocol =
		typeof window !== 'undefined' && window.location.protocol === 'https:' ? 'wss:' : 'ws:';
	const baseUrl = import.meta.env.VITE_WS_URL || `${wsProtocol}//localhost:8000/ws/analyze`;

	// Add credentials to URL query params instead of the first message body to authenticate before accepting connection
	let urlWithParams = baseUrl;
	if (opts.token) {
		const params = new URLSearchParams();
		params.append('token', opts.token);
		if (opts.encryptionKey) {
			params.append('enc_key', opts.encryptionKey);
		}
		urlWithParams += `?${params.toString()}`;
	}

	const ws = new WebSocket(urlWithParams);
	let open = false;

	ws.onopen = async () => {
		open = true;
		try {
			// Build the message
			const message: Record<string, unknown> = {
				language: opts.language
			};

			if (opts.savedStatementIds && opts.savedStatementIds.length > 0) {
				message.type = 'use_saved_statements';
				message.statement_ids = opts.savedStatementIds;
				if (opts.files.length > 0) {
					message.files = await filesToPayload(opts.files);
				}
			} else {
				message.type = 'upload_files';
				message.files = await filesToPayload(opts.files);
			}

			ws.send(JSON.stringify(message));
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
		} catch {
			// Silently ignore malformed messages in production
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
