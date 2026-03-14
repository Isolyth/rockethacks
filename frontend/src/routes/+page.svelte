<script lang="ts">
	import { goto } from "$app/navigation";
	import FileUpload from "$lib/components/FileUpload.svelte";
	import ProgressBar from "$lib/components/ProgressBar.svelte";
	import Report from "$lib/components/Report.svelte";
	import PodcastPlayer from "$lib/components/PodcastPlayer.svelte";
	import DocumentRequestCard from "$lib/components/DocumentRequest.svelte";
	import QuestionCard from "$lib/components/QuestionCard.svelte";
	import ThinkingIndicator from "$lib/components/ThinkingIndicator.svelte";
	import AdvisorChat from "$lib/components/AdvisorChat.svelte";
	import { startAnalysis, type AnalysisHandle } from "$lib/api";
	import { auth, isAuthenticated } from "$lib/stores/auth.svelte";
	import type {
		AppState,
		ProgressEvent,
		FinancialReport,
		PodcastAudio,
		DocumentRequest,
		AgentQuestion,
	} from "$lib/types";

	let appState = $state<AppState>("idle");
	let guestMode = $state(false);
	let progress = $state<ProgressEvent>({
		step: "parsing",
		message: "",
		percent: 0,
	});
	let report = $state<FinancialReport | null>(null);
	let podcastAudio = $state<PodcastAudio | null>(null);
	let errorMessage = $state("");
	let documentRequest = $state<DocumentRequest | null>(null);
	let agentQuestion = $state<AgentQuestion | null>(null);
	let thinkingText = $state("");
	let analysisHandle = $state<AnalysisHandle | null>(null);

	let stillProcessing = $derived(
		appState === "processing" && report !== null,
	);
	let showHero = $derived(!guestMode && !auth.loading && !auth.user);

	// Redirect authenticated users straight to dashboard
	$effect(() => {
		if (!auth.loading && isAuthenticated() && !guestMode && appState === "idle") {
			goto("/dashboard");
		}
	});

	function handleUpload(files: File[], language: string) {
		appState = "processing";
		progress = {
			step: "parsing",
			message: "Uploading files...",
			percent: 5,
		};
		errorMessage = "";
		report = null;
		podcastAudio = null;

		analysisHandle = startAnalysis({
			files,
			language,
			onProgress: (evt) => {
				progress = evt;
				thinkingText = "";
			},
			onReportReady: (rpt) => {
				report = rpt;
			},
			onPodcastAudioReady: (audio) => {
				podcastAudio = audio;
				appState = "done";
				analysisHandle = null;
			},
			onError: (msg) => {
				errorMessage = msg;
				appState = "error";
				analysisHandle = null;
			},
			onDocumentRequest: (req) => {
				documentRequest = req;
				appState = "awaiting_documents";
				thinkingText = "";
				progress = {
					step: "analyzing",
					message: "Agent needs additional information",
					percent: 50,
				};
			},
			onAskQuestion: (q) => {
				agentQuestion = q;
				appState = "awaiting_answer";
				thinkingText = "";
				progress = {
					step: "analyzing",
					message: "Agent has a question for you",
					percent: 50,
				};
			},
			onThinking: (text) => {
				thinkingText = text;
			},
		});
	}

	async function handleDocumentResponse(
		action: "upload" | "skip",
		files?: File[],
	) {
		if (!analysisHandle) return;
		await analysisHandle.respond(action, files);
		appState = "processing";
		progress = {
			step: "analyzing",
			message: "Continuing analysis...",
			percent: 55,
		};
		documentRequest = null;
	}

	function handleQuestionAnswer(answer: string) {
		if (!analysisHandle) return;
		analysisHandle.answerQuestion(answer);
		appState = "processing";
		progress = {
			step: "analyzing",
			message: "Continuing analysis...",
			percent: 55,
		};
		agentQuestion = null;
	}

	function reset() {
		if (analysisHandle) {
			analysisHandle.close();
			analysisHandle = null;
		}
		appState = "idle";
		report = null;
		podcastAudio = null;
		errorMessage = "";
		documentRequest = null;
		agentQuestion = null;
		thinkingText = "";
		progress = { step: "parsing", message: "", percent: 0 };
	}

	function handleBack() {
		if (appState !== "idle") {
			reset();
		} else if (guestMode) {
			guestMode = false;
		}
	}
</script>

<svelte:head>
	<title>Easy MonAI - Bank Statement Analyzer</title>
</svelte:head>

<main>
	<div class="content">
		{#if !showHero && (guestMode || appState !== "idle")}
			<div class="top-bar">
				<button class="back-btn" onclick={handleBack} type="button">
					<span class="back-icon">←</span> Back
				</button>
			</div>
		{/if}
		{#if showHero}
			<div class="hero">
				<img src="/logo.svg" alt="Easy MonAI" class="hero-logo" />
				<p class="tagline">
					Your financial life, analyzed and narrated by AI
				</p>
				<div class="hero-actions">
					<button class="primary-btn" onclick={() => goto("/login")}
						>Log In / Sign Up</button
					>
					<button class="ghost-btn" onclick={() => (guestMode = true)}
						>Continue as Guest</button
					>
				</div>
			</div>
		{:else if appState === "idle"}
			<FileUpload onupload={handleUpload} />
		{:else if appState === "awaiting_documents" && documentRequest}
			<ProgressBar {progress} />
			<DocumentRequestCard
				request={documentRequest}
				onrespond={handleDocumentResponse}
			/>
		{:else if appState === "awaiting_answer" && agentQuestion}
			<ProgressBar {progress} />
			<QuestionCard
				question={agentQuestion}
				onAnswer={handleQuestionAnswer}
			/>
		{:else if appState === "error"}
			<div class="error-card">
				<p class="error-icon">!</p>
				<p class="error-message">{errorMessage}</p>
				<button class="reset-btn" onclick={reset} type="button"
					>Try again</button
				>
			</div>
		{:else if report}
			<div class="results-grid">
				<div class="results-col results-col--left">
					<Report {report} />
				</div>
				<div class="results-col results-col--right">
					{#if stillProcessing}
						<ProgressBar {progress} />
						<p class="generating-hint">
							Generating your podcast...
						</p>
					{/if}
					{#if podcastAudio}
						<PodcastPlayer
							podcastScript={podcastAudio.podcast_script}
							audioBase64={podcastAudio.audio_base64}
							sentences={podcastAudio.sentences}
						/>
					{/if}
					{#if appState === "done" && report}
						<AdvisorChat {report} />
					{/if}
				</div>
			</div>

			{#if appState === "done"}
				<button class="reset-btn" onclick={reset} type="button"
					>Analyze more statements</button
				>
			{/if}
		{:else if appState === "processing"}
			<ProgressBar {progress} />
			{#if progress.step === "analyzing"}
				<ThinkingIndicator text={thinkingText} />
			{/if}
		{/if}
	</div>
</main>

<style>
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

	.hero-logo {
		height: 80px;
		width: auto;
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
		background: var(--gradient-gold-btn);
		color: #0a0a0f;
		border: 2px solid var(--color-gold-border);
		border-radius: var(--radius-pill);
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		transition: filter 0.2s;
		box-shadow: var(--gold-btn-shadow);
	}

	.primary-btn:hover {
		filter: brightness(1.15);
	}

	.ghost-btn {
		padding: 0.875rem 1.5rem;
		background: transparent;
		color: var(--color-text);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-pill);
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s;
	}

	.ghost-btn:hover {
		background: var(--color-surface-2);
		border-color: var(--color-accent);
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
