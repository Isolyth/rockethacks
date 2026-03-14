<script lang="ts">
	import type { FinancialReport } from '$lib/types';

	let { report }: { report: FinancialReport } = $props();

	function formatCurrency(n: number): string {
		return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n);
	}

	const maxCategoryTotal = $derived(
		Math.max(...report.categories.map((c) => c.total), 1)
	);

	const categoryColors = [
		'#6366f1', '#8b5cf6', '#a78bfa', '#c084fc',
		'#e879f9', '#f472b6', '#fb7185', '#f87171',
		'#fb923c', '#fbbf24', '#a3e635', '#34d399',
	];
</script>

<div class="report">
	<h2>Financial Report</h2>
	<p class="date-range">{report.summary.date_range}</p>

	<div class="summary-cards">
		<div class="card income">
			<span class="card-label">Income</span>
			<span class="card-value">{formatCurrency(report.summary.total_income)}</span>
		</div>
		<div class="card expenses">
			<span class="card-label">Expenses</span>
			<span class="card-value">{formatCurrency(report.summary.total_expenses)}</span>
		</div>
		<div class="card savings" class:negative={report.summary.net_savings < 0}>
			<span class="card-label">Net Savings</span>
			<span class="card-value">{formatCurrency(report.summary.net_savings)}</span>
		</div>
	</div>

	<section class="section">
		<h3>Spending by Category</h3>
		<div class="categories">
			{#each report.categories as cat, i}
				<div class="category-row">
					<div class="category-info">
						<span class="category-name">{cat.name}</span>
						<span class="category-amount">{formatCurrency(cat.total)}</span>
					</div>
					<div class="category-bar-track">
						<div
							class="category-bar-fill"
							style="width: {(cat.total / maxCategoryTotal) * 100}%; background: {categoryColors[i % categoryColors.length]}"
						></div>
					</div>
					<span class="category-pct">{cat.percentage.toFixed(1)}%</span>
				</div>
			{/each}
		</div>
	</section>

	{#if report.top_merchants.length > 0}
		<section class="section">
			<h3>Top Merchants</h3>
			<div class="merchants">
				{#each report.top_merchants as merchant}
					<div class="merchant-row">
						<span class="merchant-name">{merchant.name}</span>
						<span class="merchant-count">{merchant.count} txns</span>
						<span class="merchant-total">{formatCurrency(merchant.total)}</span>
					</div>
				{/each}
			</div>
		</section>
	{/if}

	{#if report.insights.length > 0}
		<section class="section">
			<h3>Insights</h3>
			<ul class="insights">
				{#each report.insights as insight}
					<li>{insight}</li>
				{/each}
			</ul>
		</section>
	{/if}

	{#if report.grounding?.sources && report.grounding.sources.length > 0}
		<section class="section">
			<h3>Sources</h3>
			<ul class="sources">
				{#each report.grounding.sources as source}
					<li class="source-item">
						<a href={source.uri} target="_blank" rel="noopener noreferrer">
							{source.title || source.domain || source.uri}
						</a>
						{#if source.domain}
							<span class="source-domain">{source.domain}</span>
						{/if}
					</li>
				{/each}
			</ul>
		</section>
	{/if}

	{#if report.grounding?.search_entry_point_html}
		<section class="section search-entry-point">
			{@html report.grounding.search_entry_point_html}
		</section>
	{/if}
</div>

<style>
	.report {
		width: 100%;
	}

	h2 {
		font-size: 1.5rem;
		margin-bottom: 0.25rem;
	}

	.date-range {
		color: var(--color-text-muted);
		font-size: 0.875rem;
		margin-bottom: 1.5rem;
	}

	.summary-cards {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
		gap: 1rem;
		margin-bottom: 2rem;
	}

	.card {
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		padding: 1.25rem;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.card-label {
		font-size: 0.8rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--color-text-muted);
	}

	.card-value {
		font-size: 1.5rem;
		font-weight: 700;
	}

	.card.income .card-value {
		color: var(--color-success);
	}

	.card.expenses .card-value {
		color: var(--color-danger);
	}

	.card.savings .card-value {
		color: var(--color-success);
	}

	.card.savings.negative .card-value {
		color: var(--color-danger);
	}

	.section {
		margin-bottom: 2rem;
	}

	.section h3 {
		font-size: 1.1rem;
		margin-bottom: 1rem;
		color: var(--color-text);
	}

	.categories {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.category-row {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.category-info {
		width: 200px;
		flex-shrink: 0;
		display: flex;
		justify-content: space-between;
		gap: 0.5rem;
	}

	.category-name {
		font-size: 0.875rem;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.category-amount {
		font-size: 0.875rem;
		color: var(--color-text-muted);
		flex-shrink: 0;
	}

	.category-bar-track {
		flex: 1;
		height: 8px;
		background: var(--color-surface);
		border-radius: 4px;
		overflow: hidden;
	}

	.category-bar-fill {
		height: 100%;
		border-radius: 4px;
		transition: width 0.5s ease;
	}

	.category-pct {
		width: 48px;
		text-align: right;
		font-size: 0.8rem;
		color: var(--color-text-muted);
	}

	.merchants {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.merchant-row {
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 0.75rem 1rem;
		background: var(--color-surface);
		border-radius: var(--radius-sm);
		border: 1px solid var(--color-border);
	}

	.merchant-name {
		flex: 1;
		font-size: 0.9rem;
	}

	.merchant-count {
		font-size: 0.8rem;
		color: var(--color-text-muted);
	}

	.merchant-total {
		font-size: 0.9rem;
		font-weight: 600;
	}

	.insights {
		list-style: none;
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.insights li {
		padding: 0.75rem 1rem;
		background: var(--color-surface);
		border-radius: var(--radius-sm);
		border-left: 3px solid var(--color-primary);
		font-size: 0.9rem;
		line-height: 1.5;
	}

	.sources {
		list-style: none;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.source-item {
		padding: 0.5rem 1rem;
		background: var(--color-surface);
		border-radius: var(--radius-sm);
		border: 1px solid var(--color-border);
		font-size: 0.85rem;
	}

	.source-item a {
		color: var(--color-primary);
		text-decoration: none;
	}

	.source-item a:hover {
		text-decoration: underline;
	}

	.source-domain {
		color: var(--color-text-muted);
		font-size: 0.75rem;
		margin-left: 0.5rem;
	}

	.search-entry-point {
		padding: 0.75rem 1rem;
		background: var(--color-surface);
		border-radius: var(--radius-sm);
		border: 1px solid var(--color-border);
	}
</style>
