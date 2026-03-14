import type { ProgressEvent, AnalysisResult } from './types';

export async function uploadAndAnalyze(
	files: File[],
	onProgress: (event: ProgressEvent) => void,
	onResult: (result: AnalysisResult) => void,
	onError: (message: string) => void
): Promise<void> {
	const formData = new FormData();
	files.forEach((f) => formData.append('files', f));

	let response: Response;
	try {
		response = await fetch('http://localhost:8000/analyze', {
			method: 'POST',
			body: formData
		});
	} catch {
		onError('Could not connect to the server. Is the backend running?');
		return;
	}

	if (!response.ok || !response.body) {
		onError(`Upload failed with status ${response.status}`);
		return;
	}

	const reader = response.body.getReader();
	const decoder = new TextDecoder();
	let buffer = '';

	while (true) {
		const { done, value } = await reader.read();
		if (done) {
			if (buffer.trim()) {
				processEventBlock(buffer, onProgress, onResult, onError);
			}
			break;
		}

		// Normalize \r\n to \n so the parser works regardless of server separator
		const chunk = decoder.decode(value, { stream: true }).replace(/\r/g, '');
		buffer += chunk;

		const events = buffer.split('\n\n');
		buffer = events.pop() || '';

		for (const eventBlock of events) {
			processEventBlock(eventBlock, onProgress, onResult, onError);
		}
	}
}

function processEventBlock(
	block: string,
	onProgress: (event: ProgressEvent) => void,
	onResult: (result: AnalysisResult) => void,
	onError: (message: string) => void
) {
	if (!block.trim()) return;

	let eventType = '';
	const dataLines: string[] = [];

	for (const line of block.split('\n')) {
		if (line.startsWith('event:')) {
			eventType = line.slice(6).trim();
		} else if (line.startsWith('data:')) {
			dataLines.push(line.slice(5));
		}
	}

	if (!dataLines.length) return;

	const dataStr = dataLines.join('\n').trim();
	try {
		const data = JSON.parse(dataStr);
		if (eventType === 'progress') onProgress(data);
		else if (eventType === 'result') onResult(data);
		else if (eventType === 'error') onError(data.message);
	} catch {
		// skip malformed events
	}
}
