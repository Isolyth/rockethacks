<script lang="ts">
	import FileUpload from '$lib/components/FileUpload.svelte';
	import ProgressBar from '$lib/components/ProgressBar.svelte';
	import Report from '$lib/components/Report.svelte';
	import PodcastScript from '$lib/components/PodcastScript.svelte';
	import DocumentRequestCard from '$lib/components/DocumentRequest.svelte';
	import { startAnalysis, type AnalysisHandle } from '$lib/api';
	import type { AppState, ProgressEvent, AnalysisResult, DocumentRequest } from '$lib/types';

	let appState = $state<AppState>('idle');
	let progress = $state<ProgressEvent>({ step: 'parsing', message: '', percent: 0 });
	let result = $state<AnalysisResult | null>(null);
	let errorMessage = $state('');
	let documentRequest = $state<DocumentRequest | null>(null);
	let analysisHandle = $state<AnalysisHandle | null>(null);

	function handleUpload(files: File[]) {
		appState = 'processing';
		progress = { step: 'parsing', message: 'Uploading files...', percent: 5 };
		errorMessage = '';

		analysisHandle = startAnalysis(
			files,
			(evt) => {
				progress = evt;
			},
			(res) => {
				result = res;
				appState = 'done';
				analysisHandle = null;
			},
			(msg) => {
				errorMessage = msg;
				appState = 'error';
				analysisHandle = null;
			},
			(req) => {
				documentRequest = req;
				appState = 'awaiting_documents';
				progress = { step: 'analyzing', message: 'Agent needs additional information', percent: 50 };
			}
		);
	}

	async function handleDocumentResponse(action: 'upload' | 'skip', files?: File[]) {
		if (!analysisHandle) return;
		await analysisHandle.respond(action, files);
		appState = 'processing';
		progress = { step: 'analyzing', message: 'Continuing analysis...', percent: 55 };
		documentRequest = null;
	}

	function reset() {
		if (analysisHandle) {
			analysisHandle.close();
			analysisHandle = null;
		}
		appState = 'idle';
		result = null;
		errorMessage = '';
		documentRequest = null;
		progress = { step: 'parsing', message: '', percent: 0 };
	}
</script>

<svelte:head>
	<title>StatementPod - Bank Statement Analyzer</title>
</svelte:head>

<main>
	<div class="content">
		{#if appState === 'idle'}
			<FileUpload onupload={handleUpload} />
		{:else if appState === 'processing'}
			<ProgressBar {progress} />
		{:else if appState === 'awaiting_documents' && documentRequest}
			<ProgressBar {progress} />
			<DocumentRequestCard request={documentRequest} onrespond={handleDocumentResponse} />
		{:else if appState === 'done' && result}
			<Report report={result.report} />
			<PodcastScript script={result.podcast_script} />
			<button class="reset-btn" onclick={reset} type="button">Analyze more statements</button>
		{:else if appState === 'error'}
			<div class="error-card">
				<p class="error-icon">!</p>
				<p class="error-message">{errorMessage}</p>
				<button class="reset-btn" onclick={reset} type="button">Try again</button>
			</div>
		{/if}
	</div>
</main>

<style>
	main {
		min-height: 100vh;
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: 3rem 1.5rem;
	}

	.content {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 2.5rem;
		width: 100%;
	}

	.error-card {
		text-align: center;
		padding: 2rem;
		background: var(--color-surface);
		border: 1px solid var(--color-danger);
		border-radius: var(--radius);
		max-width: 480px;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 1rem;
	}

	.error-icon {
		width: 48px;
		height: 48px;
		border-radius: 50%;
		background: var(--color-danger);
		color: white;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.5rem;
		font-weight: 700;
	}

	.error-message {
		color: var(--color-text-muted);
		font-size: 0.95rem;
	}

	.reset-btn {
		padding: 0.75rem 1.5rem;
		background: var(--color-surface-2);
		color: var(--color-text);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		font-size: 0.9rem;
		transition: all 0.2s;
	}

	.reset-btn:hover {
		border-color: var(--color-primary);
		background: var(--color-surface);
	}
</style>
