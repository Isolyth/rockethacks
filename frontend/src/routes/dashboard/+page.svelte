<script lang="ts">
	import { goto } from '$app/navigation';
	import { fetchReports, fetchStatements, deleteReport, deleteStatement } from '$lib/api';
	import { auth, isAuthenticated } from '$lib/stores/auth.svelte';
	import type { ReportSummaryItem, StatementItem } from '$lib/types';

	let reports = $state<ReportSummaryItem[]>([]);
	let statements = $state<StatementItem[]>([]);
	let loading = $state(true);
	let activeTab = $state<'reports' | 'statements'>('reports');
	let dataLoaded = false;

	$effect(() => {
		if (auth.loading) return;
		if (!isAuthenticated()) {
			goto('/login');
			return;
		}
		if (!dataLoaded) {
			dataLoaded = true;
			loadData();
		}
	});

	async function loadData() {
		loading = true;
		try {
			const [r, s] = await Promise.all([
				fetchReports(auth.token!),
				fetchStatements(auth.token!)
			]);
			reports = r;
			statements = s;
		} catch (e) {
			console.error('Failed to load dashboard data:', e);
		}
		loading = false;
	}

	async function handleDeleteReport(id: string) {
		try {
			await deleteReport(auth.token!, id);
			reports = reports.filter((r) => r.id !== id);
		} catch (e) {
			console.error('Failed to delete report:', e);
		}
	}

	async function handleDeleteStatement(id: string) {
		try {
			await deleteStatement(auth.token!, id);
			statements = statements.filter((s) => s.id !== id);
		} catch (e) {
			console.error('Failed to delete statement:', e);
		}
	}

	function formatCurrency(n: number): string {
		return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n);
	}

	function formatDate(iso: string): string {
		return new Date(iso).toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric',
			year: 'numeric'
		});
	}

	function formatSize(bytes: number): string {
		if (bytes < 1024) return `${bytes} B`;
		if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
		return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
	}
</script>

<svelte:head>
	<title>Dashboard - Easy MonAI</title>
</svelte:head>

<main>
	<div class="dashboard">
		<div class="dashboard-header">
			<h1>Dashboard</h1>
			<button class="primary-btn" onclick={() => goto('/analyze')}>New Analysis</button>
		</div>

		<div class="tabs">
			<button
				class="tab"
				class:active={activeTab === 'reports'}
				onclick={() => (activeTab = 'reports')}
			>
				Reports ({reports.length})
			</button>
			<button
				class="tab"
				class:active={activeTab === 'statements'}
				onclick={() => (activeTab = 'statements')}
			>
				Statements ({statements.length})
			</button>
		</div>

		{#if loading}
			<p class="loading">Loading...</p>
		{:else if activeTab === 'reports'}
			{#if reports.length === 0}
				<div class="empty">
					<p>No reports yet.</p>
					<button class="primary-btn" onclick={() => goto('/analyze')}>Start your first analysis</button>
				</div>
			{:else}
				<div class="card-grid">
					{#each reports as report (report.id)}
						<div class="card">
							<div class="card-header">
								<h3>{report.title}</h3>
								<span class="card-date">{formatDate(report.created_at)}</span>
							</div>
							<div class="card-stats">
								<div class="stat">
									<span class="stat-label">Income</span>
									<span class="stat-value income">{formatCurrency(report.total_income)}</span>
								</div>
								<div class="stat">
									<span class="stat-label">Expenses</span>
									<span class="stat-value expense">{formatCurrency(report.total_expenses)}</span>
								</div>
								<div class="stat">
									<span class="stat-label">Net</span>
									<span class="stat-value" class:income={report.net_savings >= 0} class:expense={report.net_savings < 0}>
										{formatCurrency(report.net_savings)}
									</span>
								</div>
							</div>
							<div class="card-actions">
								<button class="view-btn" onclick={() => goto(`/dashboard/report/${report.id}`)}>View</button>
								<button class="delete-btn" onclick={() => handleDeleteReport(report.id)}>Delete</button>
							</div>
						</div>
					{/each}
				</div>
			{/if}
		{:else}
			{#if statements.length === 0}
				<div class="empty">
					<p>No saved statements yet. Upload statements during analysis to save them.</p>
				</div>
			{:else}
				<div class="card-grid">
					{#each statements as stmt (stmt.id)}
						<div class="card card-compact">
							<div class="card-header">
								<h3>{stmt.filename}</h3>
								<span class="card-date">{formatDate(stmt.uploaded_at)}</span>
							</div>
							<div class="card-meta">
								<span class="badge">{stmt.file_type.toUpperCase()}</span>
								<span>{formatSize(stmt.file_size)}</span>
							</div>
							<div class="card-actions">
								<button class="delete-btn" onclick={() => handleDeleteStatement(stmt.id)}>Delete</button>
							</div>
						</div>
					{/each}
				</div>
			{/if}
		{/if}
	</div>
</main>

<style>
	main {
		min-height: 100vh;
		padding: 2rem 1.5rem;
	}

	.dashboard {
		max-width: 1000px;
		margin: 0 auto;
	}

	.dashboard-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1.5rem;
	}

	h1 {
		font-size: 1.75rem;
		font-weight: 700;
		margin: 0;
	}

	.primary-btn {
		padding: 0.625rem 1.25rem;
		background: var(--color-primary);
		color: white;
		border: none;
		border-radius: var(--radius-sm);
		font-size: 0.9rem;
		font-weight: 600;
		cursor: pointer;
		transition: opacity 0.2s;
	}

	.primary-btn:hover {
		opacity: 0.9;
	}

	.tabs {
		display: flex;
		gap: 0;
		border-bottom: 1px solid var(--color-border);
		margin-bottom: 1.5rem;
	}

	.tab {
		padding: 0.75rem 1.25rem;
		background: transparent;
		color: var(--color-text-muted);
		border: none;
		border-bottom: 2px solid transparent;
		font-size: 0.9rem;
		cursor: pointer;
		transition: all 0.2s;
	}

	.tab.active {
		color: var(--color-text);
		border-bottom-color: var(--color-primary);
	}

	.tab:hover:not(.active) {
		color: var(--color-text);
	}

	.loading {
		text-align: center;
		color: var(--color-text-muted);
		padding: 3rem;
	}

	.empty {
		text-align: center;
		padding: 3rem;
		color: var(--color-text-muted);
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 1rem;
	}

	.card-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
		gap: 1rem;
	}

	.card {
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		padding: 1.25rem;
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.card-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 0.5rem;
	}

	.card-header h3 {
		margin: 0;
		font-size: 0.95rem;
		font-weight: 600;
		flex: 1;
		min-width: 0;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.card-date {
		font-size: 0.75rem;
		color: var(--color-text-muted);
		white-space: nowrap;
	}

	.card-stats {
		display: flex;
		gap: 1rem;
	}

	.stat {
		display: flex;
		flex-direction: column;
		gap: 0.125rem;
	}

	.stat-label {
		font-size: 0.7rem;
		color: var(--color-text-muted);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.stat-value {
		font-size: 0.9rem;
		font-weight: 600;
	}

	.income {
		color: var(--color-success);
	}

	.expense {
		color: var(--color-danger);
	}

	.card-meta {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		font-size: 0.8rem;
		color: var(--color-text-muted);
	}

	.badge {
		padding: 0.125rem 0.5rem;
		background: var(--color-surface-2);
		border-radius: 4px;
		font-size: 0.7rem;
		font-weight: 600;
		letter-spacing: 0.05em;
	}

	.card-actions {
		display: flex;
		gap: 0.5rem;
		margin-top: 0.25rem;
	}

	.view-btn {
		padding: 0.375rem 0.75rem;
		background: var(--color-surface-2);
		color: var(--color-text);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		font-size: 0.8rem;
		cursor: pointer;
		transition: all 0.2s;
	}

	.view-btn:hover {
		border-color: var(--color-primary);
	}

	.delete-btn {
		padding: 0.375rem 0.75rem;
		background: transparent;
		color: var(--color-text-muted);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		font-size: 0.8rem;
		cursor: pointer;
		transition: all 0.2s;
	}

	.delete-btn:hover {
		border-color: var(--color-danger);
		color: var(--color-danger);
	}
</style>
