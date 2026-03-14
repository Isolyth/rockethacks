<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { fetchReport } from '$lib/api';
	import { auth, isAuthenticated } from '$lib/stores/auth.svelte';
	import Report from '$lib/components/Report.svelte';
	import PodcastPlayer from '$lib/components/PodcastPlayer.svelte';
	import AdvisorChat from '$lib/components/AdvisorChat.svelte';
	import type { ReportDetail } from '$lib/types';

	let reportData = $state<ReportDetail | null>(null);
	let loading = $state(true);
	let error = $state('');
	let dataLoaded = false;

	let reportId = $derived($page.params.id ?? '');

	$effect(() => {
		if (auth.loading) return;
		if (!isAuthenticated()) {
			goto('/login');
			return;
		}
		if (!dataLoaded) {
			dataLoaded = true;
			fetchReport(auth.token!, reportId)
				.then((data) => (reportData = data))
				.catch((e: any) => (error = e.message || 'Failed to load report'))
				.finally(() => (loading = false));
		}
	});
</script>

<svelte:head>
	<title>{reportData?.title || 'Report'} - Easy MonAI</title>
</svelte:head>

<main>
	{#if loading}
		<p class="loading">Loading report...</p>
	{:else if error}
		<div class="error-card">
			<p>{error}</p>
			<button onclick={() => goto('/dashboard')}>Back to Dashboard</button>
		</div>
	{:else if reportData}
		<div class="report-header">
			<button class="back-btn" onclick={() => goto('/dashboard')}>&larr; Dashboard</button>
			<h1>{reportData.title}</h1>
			<p class="report-date">
				{new Date(reportData.created_at).toLocaleDateString('en-US', {
					month: 'long',
					day: 'numeric',
					year: 'numeric'
				})}
			</p>
			{#if reportData.statements.length > 0}
				<div class="statements-used">
					<span class="label">Statements used:</span>
					{#each reportData.statements as stmt}
						<span class="badge">{stmt.filename}</span>
					{/each}
				</div>
			{/if}
		</div>

		<div class="results-grid">
			<div class="results-col">
				<Report report={reportData.report} />
			</div>
			<div class="results-col">
				<PodcastPlayer
					podcastScript={reportData.podcast_script}
					audioBase64={null}
					audioUrl={reportData.audio_url}
					sentences={reportData.sentences}
				/>
				<AdvisorChat report={reportData.report} language={reportData.language} />
			</div>
		</div>

		<div class="actions">
			<button class="action-btn" onclick={() => goto(`/analyze?reuse=${reportId}`)}>
				Re-analyze with these statements
			</button>
		</div>
	{/if}
</main>

<style>
	main {
		min-height: 100vh;
		padding: 2rem 1.5rem;
		max-width: 1400px;
		margin: 0 auto;
	}

	.loading {
		text-align: center;
		color: var(--color-text-muted);
		padding: 3rem;
	}

	.error-card {
		text-align: center;
		padding: 2rem;
		color: var(--color-danger);
	}

	.report-header {
		margin-bottom: 2rem;
	}

	.back-btn {
		background: none;
		border: none;
		color: var(--color-text-muted);
		cursor: pointer;
		font-size: 0.875rem;
		padding: 0;
		margin-bottom: 0.75rem;
	}

	.back-btn:hover {
		color: var(--color-text);
	}

	h1 {
		font-size: 1.5rem;
		font-weight: 700;
		margin: 0 0 0.25rem;
	}

	.report-date {
		color: var(--color-text-muted);
		font-size: 0.875rem;
		margin: 0 0 0.75rem;
	}

	.statements-used {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		flex-wrap: wrap;
	}

	.label {
		font-size: 0.8rem;
		color: var(--color-text-muted);
	}

	.badge {
		padding: 0.125rem 0.5rem;
		background: var(--color-surface-2);
		border-radius: 4px;
		font-size: 0.75rem;
	}

	.results-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 2.5rem;
		align-items: start;
	}

	.results-col {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
		min-width: 0;
	}

	.actions {
		margin-top: 2rem;
		text-align: center;
	}

	.action-btn {
		padding: 0.75rem 1.5rem;
		background: var(--color-surface-2);
		color: var(--color-text);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		font-size: 0.9rem;
		cursor: pointer;
		transition: all 0.2s;
	}

	.action-btn:hover {
		border-color: var(--color-primary);
	}

	@media (max-width: 768px) {
		.results-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
