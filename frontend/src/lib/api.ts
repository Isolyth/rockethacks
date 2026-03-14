import type { ProgressEvent, AnalysisResult, DocumentRequest } from './types';

export interface AnalysisHandle {
	respond: (action: 'upload' | 'skip', files?: File[]) => Promise<void>;
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
	onProgress: (event: ProgressEvent) => void,
	onResult: (result: AnalysisResult) => void,
	onError: (message: string) => void,
	onDocumentRequest: (request: DocumentRequest) => void
): AnalysisHandle {
	const ws = new WebSocket('ws://localhost:8000/ws/analyze');
	let open = false;

	ws.onopen = async () => {
		open = true;
		try {
			const payload = await filesToPayload(files);
			ws.send(
				JSON.stringify({
					type: 'upload_files',
					files: payload
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
				case 'request_documents':
					onDocumentRequest(data);
					break;
				case 'result':
					onResult(data);
					break;
				case 'error':
					onError(data.message);
					break;
			}
		} catch {
			// skip malformed messages
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
		close() {
			if (open) ws.close();
		}
	};
}
