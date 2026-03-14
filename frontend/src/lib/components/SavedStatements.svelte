<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchStatements } from '$lib/api';
	import { auth } from '$lib/stores/auth.svelte';
	import type { StatementItem } from '$lib/types';

	let { selected = $bindable<string[]>([]) }: { selected?: string[] } = $props();

	let statements = $state<StatementItem[]>([]);
	let loading = $state(true);

	onMount(async () => {
		if (auth.token) {
			try {
				statements = await fetchStatements(auth.token);
			} catch (e) {
				console.error('Failed to fetch statements:', e);
			}
		}
		loading = false;
	});

	function toggle(id: string) {
		if (selected.includes(id)) {
			selected = selected.filter((s) => s !== id);
		} else {
			selected = [...selected, id];
		}
	}

	function formatSize(bytes: number): string {
		if (bytes < 1024) return `${bytes} B`;
		if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
		return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
	}
</script>

{#if loading}
	<p class="loading">Loading saved statements...</p>
{:else if statements.length > 0}
	<div class="saved-statements">
		<h3>Saved Statements</h3>
		<p class="hint">Select statements to include in your analysis</p>
		<div class="list">
			{#each statements as stmt (stmt.id)}
				<label class="stmt-item" class:checked={selected.includes(stmt.id)}>
					<input
						type="checkbox"
						checked={selected.includes(stmt.id)}
						onchange={() => toggle(stmt.id)}
					/>
					<div class="stmt-info">
						<span class="stmt-name">{stmt.filename}</span>
						<span class="stmt-meta">
							<span class="badge">{stmt.file_type.toUpperCase()}</span>
							{formatSize(stmt.file_size)}
						</span>
					</div>
				</label>
			{/each}
		</div>
		{#if selected.length > 0}
			<p class="selected-count">{selected.length} statement{selected.length > 1 ? 's' : ''} selected</p>
		{/if}
	</div>
{/if}

<style>
	.loading {
		color: var(--color-text-muted);
		font-size: 0.875rem;
	}

	.saved-statements {
		width: 100%;
		max-width: 600px;
	}

	h3 {
		font-size: 1rem;
		font-weight: 600;
		margin: 0 0 0.25rem;
	}

	.hint {
		font-size: 0.8rem;
		color: var(--color-text-muted);
		margin: 0 0 0.75rem;
	}

	.list {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.stmt-item {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.625rem 0.75rem;
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		cursor: pointer;
		transition: border-color 0.2s;
	}

	.stmt-item:hover {
		border-color: var(--color-primary);
	}

	.stmt-item.checked {
		border-color: var(--color-primary);
		background: rgba(99, 102, 241, 0.05);
	}

	.stmt-item input[type='checkbox'] {
		accent-color: var(--color-primary);
		width: 16px;
		height: 16px;
		flex-shrink: 0;
	}

	.stmt-info {
		display: flex;
		justify-content: space-between;
		align-items: center;
		flex: 1;
		min-width: 0;
	}

	.stmt-name {
		font-size: 0.875rem;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.stmt-meta {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.75rem;
		color: var(--color-text-muted);
		flex-shrink: 0;
	}

	.badge {
		padding: 0.1rem 0.4rem;
		background: var(--color-surface-2);
		border-radius: 4px;
		font-size: 0.65rem;
		font-weight: 600;
		letter-spacing: 0.05em;
	}

	.selected-count {
		font-size: 0.8rem;
		color: var(--color-primary);
		margin: 0.5rem 0 0;
	}
</style>
