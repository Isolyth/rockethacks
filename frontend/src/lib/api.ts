import type {
	ProgressEvent,
	FinancialReport,
	PodcastAudio,
	DocumentRequest,
	AgentQuestion
} from './types';

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

export function startAnalysis(
	files: File[],
	language: string,
	onProgress: (event: ProgressEvent) => void,
	onReportReady: (report: FinancialReport) => void,
	onPodcastAudioReady: (audio: PodcastAudio) => void,
	onError: (message: string) => void,
	onDocumentRequest: (request: DocumentRequest) => void,
	onAskQuestion: (question: AgentQuestion) => void,
	onThinking: (text: string) => void
): AnalysisHandle {
	const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/analyze';
	const ws = new WebSocket(wsUrl);
	let open = false;

	ws.onopen = async () => {
		open = true;
		try {
			const payload = await filesToPayload(files);
			ws.send(
				JSON.stringify({
					type: 'upload_files',
					files: payload,
					language
				})
			);
		} catch {
			onError('Failed to read files');
		}
	};

	ws.onmessage = (event) => {
		try {
			const data = JSON.parse(event.data);
			switch (data.type) {
				case 'progress':
					onProgress(data);
					break;
				case 'thinking':
					onThinking(data.text);
					break;
				case 'request_documents':
					onDocumentRequest(data);
					break;
				case 'ask_question':
					onAskQuestion(data);
					break;
				case 'report_ready':
					onReportReady(data.report);
					break;
				case 'podcast_audio_ready':
					onPodcastAudioReady(data);
					break;
				case 'error':
					onError(data.message);
					break;
			}
		} catch (e) {
			console.warn('Malformed WebSocket message:', e);
		}
	};

	ws.onerror = () => {
		onError('WebSocket connection error. Is the backend running?');
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
