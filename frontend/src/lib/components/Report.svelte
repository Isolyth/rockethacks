<script lang="ts">
	import DOMPurify from "isomorphic-dompurify";
	import type { FinancialReport } from "$lib/types";
	import QuestionCard from "$lib/components/QuestionCard.svelte";
	import { sendFollowup } from "$lib/api";
	import { auth } from "$lib/stores/auth.svelte";

	let { report }: { report: FinancialReport } = $props();

	// svelte-ignore state_referenced_locally
	let currentReport = $state(report);
	let isFollowingUp = $state(false);
	let followupError = $state<string | null>(null);
	let chatHistory = $state<{ role: 'user' | 'model'; content: string }[]>([]);
	let chatInput = $state('');

	function formatCurrency(n: number): string {
		return new Intl.NumberFormat("en-US", {
			style: "currency",
			currency: "USD",
		}).format(n);
	}

	const maxCategoryTotal = $derived(
		Math.max(...currentReport.categories.map((c) => c.total), 1),
	);

	const categoryColors = [
		"#4361EE",
		"#3A0CA3",
		"#7209B7",
		"#F72585",
		"#4CC9F0",
		"#00B4D8",
		"#0077B6",
		"#023E8A",
	];

	async function submitChat() {
		const prompt = chatInput.trim();
		if (!prompt || isFollowingUp) return;

		try {
			isFollowingUp = true;
			followupError = null;
			
			// Add user message to UI immediately
			chatHistory = [...chatHistory, { role: 'user', content: prompt }];
			chatInput = '';
			
			// Get token if user is signed in, otherwise null
			const token = auth.token; 
			const result = await sendFollowup(token, currentReport, prompt, chatHistory);
			
			// Add AI message to UI
			chatHistory = [...chatHistory, { role: 'model', content: result.message }];
			
		} catch (err: any) {
			followupError = err.message || "Something went wrong";
			// Remove the user message if it failed, or leave it. Leaving it is fine, but they won't get a response.
			// Ideally we could show an error state, but re-allowing submission is enough.
		} finally {
			isFollowingUp = false;
		}
	}
</script>

<div class="report">
	<div class="header-content">
		<h2>Financial Report</h2>
	</div>
	<p class="date-range">{currentReport.summary.date_range}</p>

	<div class="summary-cards">
		<div class="card income">
			<span class="card-label">Income</span>
			<span class="card-value"
				>{formatCurrency(currentReport.summary.total_income)}</span
			>
		</div>
		<div class="card expenses">
			<span class="card-label">Expenses</span>
			<span class="card-value"
				>{formatCurrency(currentReport.summary.total_expenses)}</span
			>
		</div>
		<div
			class="card savings"
			class:negative={currentReport.summary.net_savings < 0}
		>
			<span class="card-label">Net Savings</span>
			<span class="card-value"
				>{formatCurrency(currentReport.summary.net_savings)}</span
			>
		</div>
	</div>

	<section class="section">
		<h3>Spending by Category</h3>
		<div class="categories">
			{#each currentReport.categories as cat, i}
				<div class="category-row">
					<div class="category-info">
						<span class="category-name">{cat.name}</span>
						<span class="category-amount"
							>{formatCurrency(cat.total)}</span
						>
					</div>
					<div class="category-bar-track">
						<div
							class="category-bar-fill"
							style="width: {(cat.total / maxCategoryTotal) *
								100}%; background: {categoryColors[
								i % categoryColors.length
							]}"
						></div>
					</div>
					<span class="category-pct"
						>{cat.percentage.toFixed(1)}%</span
					>
				</div>
			{/each}
		</div>
	</section>

	{#if currentReport.top_merchants.length > 0}
		<section class="section">
			<h3>Top Merchants</h3>
			<div class="merchants">
				{#each currentReport.top_merchants as merchant}
					<div class="merchant-row">
						<span class="merchant-name">{merchant.name}</span>
						<span class="merchant-count">{merchant.count} txns</span
						>
						<span class="merchant-total"
							>{formatCurrency(merchant.total)}</span
						>
					</div>
				{/each}
			</div>
		</section>
	{/if}

	{#if currentReport.insights.length > 0}
		<section class="section">
			<h3>Insights</h3>
			<ul class="insights">
				{#each currentReport.insights as insight}
					<li>{insight}</li>
				{/each}
			</ul>
		</section>
	{/if}

	{#if currentReport.grounding?.sources && currentReport.grounding.sources.length > 0}
		<section class="section">
			<h3>Sources</h3>
			<ul class="sources">
				{#each currentReport.grounding.sources as source}
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

	{#if currentReport.grounding?.search_entry_point_html}
		<section class="section search-entry-point">
			{@html DOMPurify.sanitize(currentReport.grounding.search_entry_point_html)}
		</section>
	{/if}

	<div class="chat-section">
		<h3>Advisor Chat</h3>
		<p class="chat-subtitle">Ask a "what-if" question to get financial advice based on your report.</p>
		
		{#if chatHistory.length > 0}
			<div class="chat-log">
				{#each chatHistory as msg}
					<div class="chat-bubble {msg.role}">
						<div class="msg-content">{msg.content}</div>
					</div>
				{/each}
				{#if isFollowingUp}
					<div class="chat-bubble model thinking">
						<div class="msg-content">Thinking...</div>
					</div>
				{/if}
			</div>
		{/if}

		{#if followupError}
			<p class="error">{followupError}</p>
		{/if}

		<div class="chat-input-wrapper">
			<textarea
				class="chat-input"
				placeholder="e.g., What if I cut out my Starbucks spending totally?"
				bind:value={chatInput}
				disabled={isFollowingUp}
				onkeydown={(e) => {
					if (e.key === 'Enter' && !e.shiftKey && chatInput.trim() && !isFollowingUp) {
						e.preventDefault();
						submitChat();
					}
				}}
			></textarea>
			<button class="send-btn" disabled={isFollowingUp || !chatInput.trim()} onclick={submitChat}>
				Ask
			</button>
		</div>
	</div>
</div>

<style>
	.report {
		width: 100%;
		background: var(--color-surface);
		backdrop-filter: blur(12px);
		-webkit-backdrop-filter: blur(12px);
		border-radius: var(--radius);
		border: 1px solid var(--color-border);
		padding: 2rem;
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
		backdrop-filter: blur(12px);
		-webkit-backdrop-filter: blur(12px);
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

	.chat-section {
		margin-top: 3rem;
		border-top: 1px solid var(--color-border);
		padding-top: 2rem;
		display: flex;
		flex-direction: column;
	}

	.chat-subtitle {
		color: var(--color-text-muted);
		margin-bottom: 1.5rem;
		font-size: 0.95rem;
	}

	.chat-log {
		display: flex;
		flex-direction: column;
		gap: 1rem;
		margin-bottom: 1.5rem;
		max-height: 400px;
		overflow-y: auto;
		padding-right: 0.5rem;
	}

	.chat-bubble {
		max-width: 80%;
		padding: 0.85rem 1rem;
		border-radius: 12px;
		line-height: 1.5;
		font-size: 0.95rem;
	}

	.chat-bubble.user {
		align-self: flex-end;
		background: var(--color-primary);
		color: white;
		border-bottom-right-radius: 4px;
	}

	.chat-bubble.model {
		align-self: flex-start;
		background: var(--color-surface-hover);
		color: var(--color-text);
		border: 1px solid var(--color-border);
		border-bottom-left-radius: 4px;
	}

	.chat-bubble.thinking {
		opacity: 0.7;
		font-style: italic;
		animation: pulse 1.5s infinite;
	}

	.chat-input-wrapper {
		display: flex;
		gap: 0.5rem;
		align-items: flex-end;
	}

	.chat-input {
		flex: 1;
		min-height: 60px;
		max-height: 150px;
		resize: vertical;
		padding: 0.75rem 1rem;
		border-radius: var(--radius-sm);
		border: 1px solid var(--color-border);
		background: var(--color-bg);
		color: var(--color-text);
		font-family: inherit;
		font-size: 1rem;
	}

	.chat-input:focus {
		outline: none;
		border-color: var(--color-primary);
		box-shadow: 0 0 0 2px rgba(67, 97, 238, 0.2);
	}
	
	.chat-input:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.send-btn {
		background: var(--color-primary);
		color: white;
		border: none;
		border-radius: var(--radius-sm);
		padding: 0 1.5rem;
		height: 60px;
		font-weight: 600;
		cursor: pointer;
		transition: background 0.2s;
	}

	.send-btn:hover:not(:disabled) {
		background: #3651c4;
	}

	.send-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.error {
		color: var(--color-danger);
		font-size: 0.875rem;
		margin-bottom: 1rem;
	}

	.header-content {
		display: flex;
		align-items: center;
		justify-content: space-between;
	}

	@keyframes pulse {
		0% { opacity: 0.6; }
		50% { opacity: 1; }
		100% { opacity: 0.6; }
	}
</style>
