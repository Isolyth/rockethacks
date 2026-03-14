<script lang="ts">
	import FileUpload from '$lib/components/FileUpload.svelte';
	import ProgressBar from '$lib/components/ProgressBar.svelte';
	import Report from '$lib/components/Report.svelte';
	import PodcastPlayer from '$lib/components/PodcastPlayer.svelte';
	import DocumentRequestCard from '$lib/components/DocumentRequest.svelte';
	import QuestionCard from '$lib/components/QuestionCard.svelte';
	import ThinkingIndicator from '$lib/components/ThinkingIndicator.svelte';
	import { startAnalysis, type AnalysisHandle } from '$lib/api';
	import type {
		AppState,
		ProgressEvent,
		FinancialReport,
		PodcastAudio,
		DocumentRequest,
		AgentQuestion
	} from '$lib/types';

	let appState = $state<AppState>('idle');
	let userState = $state<'unauthenticated' | 'authenticated' | 'guest'>('unauthenticated');
	let progress = $state<ProgressEvent>({ step: 'parsing', message: '', percent: 0 });
	let report = $state<FinancialReport | null>(null);
	let podcastAudio = $state<PodcastAudio | null>(null);
	let errorMessage = $state('');
	let documentRequest = $state<DocumentRequest | null>(null);
	let agentQuestion = $state<AgentQuestion | null>(null);
	let thinkingText = $state('');
	let analysisHandle = $state<AnalysisHandle | null>(null);

	// Whether we're still processing (report shown but podcast still generating)
	let stillProcessing = $derived(appState === 'processing' && report !== null);

	function handleUpload(files: File[], language: string) {
		appState = 'processing';
		progress = { step: 'parsing', message: 'Uploading files...', percent: 5 };
		errorMessage = '';
		report = null;
		podcastAudio = null;

		analysisHandle = startAnalysis(
			files,
			language,
			(evt) => {
				progress = evt;
				thinkingText = '';
			},
			(rpt) => {
				report = rpt;
			},
			(audio) => {
				podcastAudio = audio;
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
				thinkingText = '';
				progress = { step: 'analyzing', message: 'Agent needs additional information', percent: 50 };
			},
			(q) => {
				agentQuestion = q;
				appState = 'awaiting_answer';
				thinkingText = '';
				progress = { step: 'analyzing', message: 'Agent has a question for you', percent: 50 };
			},
			(text) => {
				thinkingText = text;
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

	function handleQuestionAnswer(answer: string) {
		if (!analysisHandle) return;
		analysisHandle.answerQuestion(answer);
		appState = 'processing';
		progress = { step: 'analyzing', message: 'Continuing analysis...', percent: 55 };
		agentQuestion = null;
	}

	function reset() {
		if (analysisHandle) {
			analysisHandle.close();
			analysisHandle = null;
		}
		appState = 'idle';
		report = null;
		podcastAudio = null;
		errorMessage = '';
		documentRequest = null;
		agentQuestion = null;
		thinkingText = '';
		progress = { step: 'parsing', message: '', percent: 0 };
	}
</script>

<svelte:head>
	<title>Easy monAI - Bank Statement Analyzer</title>
</svelte:head>

<header class="app-header">
	<div class="header-content">
		<div class="logo">StatementPod</div>
		<div class="user-status">
			{#if userState === 'unauthenticated'}
				<button class="login-btn-small" onclick={() => userState = 'authenticated'}>Login</button>
			{:else if userState === 'authenticated'}
				<span class="status-text">Logged In</span>
			{:else if userState === 'guest'}
				<span class="status-text">Guest Mode</span>
			{/if}
		</div>
	</div>
</header>

<main>
	<div class="content">
		{#if userState === 'unauthenticated'}
			<div class="hero">
				<h1>StatementPod</h1>
				<p class="tagline">Your financial life, analyzed and narrated by AI</p>
				<div class="hero-actions">
					<button class="primary-btn" onclick={() => userState = 'authenticated'}>Log In / Sign Up</button>
					<button class="ghost-btn" onclick={() => userState = 'guest'}>Continue as Guest</button>
				</div>
			</div>
		{:else if appState === 'idle'}
			<FileUpload onupload={handleUpload} />
		{:else if appState === 'awaiting_documents' && documentRequest}
			<ProgressBar {progress} />
			<DocumentRequestCard request={documentRequest} onrespond={handleDocumentResponse} />
		{:else if appState === 'awaiting_answer' && agentQuestion}
			<ProgressBar {progress} />
			<QuestionCard question={agentQuestion} onAnswer={handleQuestionAnswer} />
		{:else if appState === 'error'}
			<div class="error-card">
				<p class="error-icon">!</p>
				<p class="error-message">{errorMessage}</p>
				<button class="reset-btn" onclick={reset} type="button">Try again</button>
			</div>
		{:else}
			{#if report}
				<!-- Two-column results layout -->
				<div class="results-grid">
					<div class="results-col results-col--left">
						<Report {report} />
					</div>
					<div class="results-col results-col--right">
						{#if stillProcessing}
							<ProgressBar {progress} />
							<p class="generating-hint">Generating your podcast...</p>
						{/if}
						{#if podcastAudio}
							<PodcastPlayer
								podcastScript={podcastAudio.podcast_script}
								audioBase64={podcastAudio.audio_base64}
								sentences={podcastAudio.sentences}
							/>
						{/if}
					</div>
				</div>

				{#if appState === 'done'}
					<button class="reset-btn" onclick={reset} type="button">Analyze more statements</button>
				{/if}
			{:else if appState === 'processing'}
				<!-- No report yet: centered progress -->
				<ProgressBar {progress} />
				{#if progress.step === 'analyzing'}
					<ThinkingIndicator text={thinkingText} />
				{/if}
			{/if}
		{/if}
	</div>
</main>

<style>
	.app-header {
		position: sticky;
		top: 0;
		width: 100%;
		background: var(--color-surface);
		border-bottom: 1px solid var(--color-border);
		z-index: 100;
	}

	.header-content {
		max-width: 1400px;
		margin: 0 auto;
		padding: 1rem 1.5rem;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.logo {
		font-weight: 700;
		font-size: 1.25rem;
		color: var(--color-text);
	}

	.login-btn-small {
		padding: 0.5rem 1rem;
		background: transparent;
		color: var(--color-text);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		font-size: 0.875rem;
		cursor: pointer;
		transition: all 0.2s;
	}

	.login-btn-small:hover {
		border-color: var(--color-primary);
	}

	.status-text {
		font-size: 0.875rem;
		color: var(--color-text-muted);
	}

	.hero {
		text-align: center;
		padding: 4rem 1rem;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 1.5rem;
		max-width: 600px;
		margin: 0 auto;
	}

	.hero h1 {
		font-size: 3.5rem;
		font-weight: 800;
		margin: 0;
		background: linear-gradient(to right, var(--color-primary), #b366ff);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
	}

	.tagline {
		font-size: 1.25rem;
		color: var(--color-text-muted);
		margin: 0;
	}

	.hero-actions {
		display: flex;
		gap: 1rem;
		margin-top: 1rem;
	}
	
	@media (max-width: 600px) {
		.hero-actions {
			flex-direction: column;
			width: 100%;
		}
		
		.hero-actions > button {
			width: 100%;
		}
	}

	.primary-btn {
		padding: 0.875rem 1.5rem;
		background: var(--color-primary);
		color: white;
		border: none;
		border-radius: var(--radius-sm);
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		transition: opacity 0.2s;
	}

	.primary-btn:hover {
		opacity: 0.9;
	}

	.ghost-btn {
		padding: 0.875rem 1.5rem;
		background: transparent;
		color: var(--color-text);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s;
	}

	.ghost-btn:hover {
		background: var(--color-surface-2);
		border-color: var(--color-text-muted);
	}

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

	.results-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 2.5rem;
		width: 100%;
		max-width: 1400px;
		align-items: start;
	}

	.results-col {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
		min-width: 0;
	}

	.generating-hint {
		text-align: center;
		color: var(--color-text-muted);
		font-size: 0.9rem;
		padding: 2rem 1rem;
		background: var(--color-surface);
		border: 1px dashed var(--color-border);
		border-radius: var(--radius);
	}

	.results-col--right :global(.progress-container) {
		max-width: none;
	}

	@media (max-width: 768px) {
		.results-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
