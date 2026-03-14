<script lang="ts">
	import { goto } from '$app/navigation';
	import FileUpload from '$lib/components/FileUpload.svelte';
	import SavedStatements from '$lib/components/SavedStatements.svelte';
	import ProgressBar from '$lib/components/ProgressBar.svelte';
	import Report from '$lib/components/Report.svelte';
	import PodcastPlayer from '$lib/components/PodcastPlayer.svelte';
	import DocumentRequestCard from '$lib/components/DocumentRequest.svelte';
	import QuestionCard from '$lib/components/QuestionCard.svelte';
	import ThinkingIndicator from '$lib/components/ThinkingIndicator.svelte';
	import AdvisorChat from '$lib/components/AdvisorChat.svelte';
	import { startAnalysis, type AnalysisHandle } from '$lib/api';
	import { auth, isAuthenticated } from '$lib/stores/auth.svelte';
	import type {
		AppState,
		ProgressEvent,
		FinancialReport,
		PodcastAudio,
		DocumentRequest,
		AgentQuestion
	} from '$lib/types';

	let appState = $state<AppState>('idle');
	let progress = $state<ProgressEvent>({ step: 'parsing', message: '', percent: 0 });
	let report = $state<FinancialReport | null>(null);
	let podcastAudio = $state<PodcastAudio | null>(null);
	let errorMessage = $state('');
	let documentRequest = $state<DocumentRequest | null>(null);
	let agentQuestion = $state<AgentQuestion | null>(null);
	let thinkingText = $state('');
	let analysisHandle = $state<AnalysisHandle | null>(null);
	let savedReportId = $state<string | null>(null);
	let selectedStatements = $state<string[]>([]);
	let selectedLanguage = $state('en');

	let stillProcessing = $derived(appState === 'processing' && report !== null);

	const languages = [
		{ code: 'en', name: 'English' },
		{ code: 'es', name: 'Spanish' },
		{ code: 'fr', name: 'French' },
		{ code: 'de', name: 'German' },
		{ code: 'pt', name: 'Portuguese' },
		{ code: 'it', name: 'Italian' },
		{ code: 'ja', name: 'Japanese' },
		{ code: 'ko', name: 'Korean' },
		{ code: 'zh', name: 'Chinese' },
		{ code: 'hi', name: 'Hindi' },
		{ code: 'ar', name: 'Arabic' },
		{ code: 'nl', name: 'Dutch' },
		{ code: 'pl', name: 'Polish' },
		{ code: 'ru', name: 'Russian' }
	];

	$effect(() => {
		if (!auth.loading && !isAuthenticated()) {
			goto('/login');
		}
	});

	function startWithSavedOnly() {
		handleUpload([], selectedLanguage);
	}

	function handleUpload(files: File[], language: string) {
		appState = 'processing';
		progress = { step: 'parsing', message: 'Uploading files...', percent: 5 };
		errorMessage = '';
		report = null;
		podcastAudio = null;
		savedReportId = null;

		analysisHandle = startAnalysis({
			files,
			language,
			token: auth.token,
			encryptionKey: auth.encryptionKey,
			savedStatementIds: selectedStatements.length > 0 ? selectedStatements : undefined,
			onProgress: (evt) => {
				progress = evt;
				thinkingText = '';
			},
			onReportReady: (rpt) => {
				report = rpt;
			},
			onPodcastAudioReady: (audio) => {
				podcastAudio = audio;
				savedReportId = (audio as any).report_id || null;
				appState = 'done';
				analysisHandle = null;
			},
			onError: (msg) => {
				errorMessage = msg;
				appState = 'error';
				analysisHandle = null;
			},
			onDocumentRequest: (req) => {
				documentRequest = req;
				appState = 'awaiting_documents';
				thinkingText = '';
				progress = {
					step: 'analyzing',
					message: 'Agent needs additional information',
					percent: 50
				};
			},
			onAskQuestion: (q) => {
				agentQuestion = q;
				appState = 'awaiting_answer';
				thinkingText = '';
				progress = { step: 'analyzing', message: 'Agent has a question for you', percent: 50 };
			},
			onThinking: (text) => {
				thinkingText = text;
			}
		});
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
		savedReportId = null;
		selectedStatements = [];
		progress = { step: 'parsing', message: '', percent: 0 };
	}

	function handleBack() {
		if (appState !== 'idle') {
			reset();
		} else {
			goto('/');
		}
	}
</script>

<svelte:head>
	<title>New Analysis - Easy MonAI</title>
</svelte:head>

<main>
	<div class="content">
		<div class="top-bar">
			<button class="back-btn" onclick={handleBack} type="button">
				<span class="back-icon">←</span> Back
			</button>
		</div>

		{#if appState === 'idle'}
			<h1>New Analysis</h1>
			<SavedStatements bind:selected={selectedStatements} />

			{#if selectedStatements.length > 0}
				<div class="saved-actions">
					<div class="language-row">
						<label class="language-label" for="lang-select">Report & podcast language</label>
						<select id="lang-select" class="language-select" bind:value={selectedLanguage}>
							{#each languages as lang}
								<option value={lang.code}>{lang.name}</option>
							{/each}
						</select>
					</div>
					<button class="primary-btn" onclick={startWithSavedOnly} type="button">
						Analyze {selectedStatements.length} saved statement{selectedStatements.length > 1 ? 's' : ''}
					</button>
					<p class="divider-text">or upload additional files below</p>
				</div>
			{/if}

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
						{#if appState === 'done' && report}
							<AdvisorChat {report} />
						{/if}
					</div>
				</div>

				{#if appState === 'done'}
					<div class="done-actions">
						{#if savedReportId}
							<button
								class="view-btn"
								onclick={() => goto(`/dashboard/report/${savedReportId}`)}
								type="button"
							>
								View in Dashboard
							</button>
						{/if}
						<button class="reset-btn" onclick={reset} type="button">
							Analyze more statements
						</button>
					</div>
				{/if}
			{:else if appState === 'processing'}
				<ProgressBar {progress} />
				{#if progress.step === 'analyzing'}
					<ThinkingIndicator text={thinkingText} />
				{/if}
			{/if}
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
		gap: 2rem;
		width: 100%;
	}

	h1 {
		font-size: 1.5rem;
		font-weight: 700;
		margin: 0;
	}

	.saved-actions {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 1rem;
		width: 100%;
		max-width: 560px;
	}

	.language-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
		width: 100%;
		padding: 0.75rem 1rem;
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
	}

	.language-label {
		font-size: 0.9rem;
		color: var(--color-text-muted);
	}

	.language-select {
		padding: 0.5rem 0.75rem;
		background: var(--color-surface-2);
		color: var(--color-text);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		font-size: 0.9rem;
		min-width: 140px;
	}

	.language-select:focus {
		outline: none;
		border-color: var(--color-accent);
	}

	.primary-btn {
		padding: 0.875rem 2rem;
		background: var(--gradient-gold-btn);
		color: #0a0a0f;
		border: 2px solid var(--color-gold-border);
		border-radius: var(--radius-pill);
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		transition: filter 0.2s;
		width: 100%;
		box-shadow: var(--gold-btn-shadow);
	}

	.primary-btn:hover {
		filter: brightness(1.15);
	}

	.divider-text {
		font-size: 0.85rem;
		color: var(--color-text-muted);
		margin: 0;
	}

	.top-bar {
		width: 100%;
		max-width: 1400px;
		display: flex;
		justify-content: flex-start;
		margin-bottom: -1rem;
	}

	.back-btn {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 1rem;
		background: transparent;
		color: var(--color-text-muted);
		border: 1px solid transparent;
		border-radius: var(--radius-sm);
		font-size: 0.95rem;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.back-btn:hover {
		color: var(--color-text);
		background: var(--color-surface-2);
		border-color: var(--color-border);
		transform: translateX(-2px);
	}

	.back-icon {
		font-size: 1.1rem;
		transition: transform 0.2s ease;
	}

	.back-btn:hover .back-icon {
		transform: translateX(-2px);
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
		box-shadow: var(--shadow-inset);
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

	.done-actions {
		display: flex;
		gap: 0.75rem;
		align-items: center;
	}

	.view-btn {
		padding: 0.75rem 1.5rem;
		background: var(--gradient-gold-btn);
		color: #0a0a0f;
		border: 2px solid var(--color-gold-border);
		border-radius: var(--radius-pill);
		font-size: 0.9rem;
		font-weight: 600;
		cursor: pointer;
		transition: filter 0.2s;
		box-shadow: var(--gold-btn-shadow);
	}

	.view-btn:hover {
		filter: brightness(1.15);
	}

	.reset-btn {
		padding: 0.75rem 1.5rem;
		background: var(--color-surface-2);
		color: var(--color-text);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-pill);
		font-size: 0.9rem;
		transition: all 0.2s;
	}

	.reset-btn:hover {
		border-color: var(--color-accent);
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
