<script lang="ts">
	import type { AgentQuestion } from '$lib/types';

	let {
		question,
		onAnswer,
		mode = 'question',
		loading = false
	}: {
		question?: AgentQuestion;
		onAnswer: (answer: string) => void;
		mode?: 'question' | 'followup';
		loading?: boolean;
	} = $props();

	let selected = $state<string | null>(null);
	let customText = $state('');
	let useCustom = $state(false);
</script>

<div class="question-card">
	<div class="question-header">
		{#if mode === 'followup'}
			<div class="question-icon followup">✨</div>
			<h3 class="question-title">Follow-up Analysis</h3>
		{:else}
			<div class="question-icon">?</div>
			<h3 class="question-title">The agent has a question</h3>
		{/if}
	</div>

	{#if mode === 'question' && question}
		<p class="question-text">{question.question}</p>

		<div class="options">
		{#each question.options as option}
			<label class="option" class:selected={!useCustom && selected === option}>
				<input
					type="radio"
					name="agent-question"
					value={option}
					checked={!useCustom && selected === option}
					onchange={() => {
						selected = option;
						useCustom = false;
					}}
				/>
				<span class="option-text">{option}</span>
			</label>
		{/each}

		<label class="option" class:selected={useCustom}>
			<input
				type="radio"
				name="agent-question"
				value="__custom__"
				checked={useCustom}
				onchange={() => {
					useCustom = true;
					selected = null;
				}}
				disabled={loading}
			/>
			<span class="option-text">Other</span>
		</label>
	</div>

	{#if useCustom}
		<input
			type="text"
			class="custom-input"
			placeholder="Type your answer..."
			bind:value={customText}
			disabled={loading}
			onkeydown={(e) => {
				if (e.key === 'Enter' && customText.trim() && !loading) onAnswer(customText.trim());
			}}
		/>
	{/if}
	{:else}
		<p class="question-text">Ask a "what-if" question to see how it affects your projection.</p>
		<textarea
			class="custom-input followup-textarea"
			placeholder="e.g., What if I cut out my Starbucks spending totally and doubled my savings?"
			bind:value={customText}
			disabled={loading}
			onkeydown={(e) => {
				if (e.key === 'Enter' && !e.shiftKey && customText.trim() && !loading) {
					e.preventDefault();
					onAnswer(customText.trim());
				}
			}}
		></textarea>
	{/if}

	<div class="actions">
		<button
			class="submit-btn"
			disabled={loading || (mode === 'question' ? (useCustom ? !customText.trim() : !selected) : !customText.trim())}
			onclick={() => {
				const answer = mode === 'question' ? (useCustom ? customText.trim() : selected) : customText.trim();
				if (answer && !loading) {
					onAnswer(answer);
					if (mode === 'followup') {
						customText = '';
					}
				}
			}}
			type="button"
		>
			{#if loading}
				Thinking...
			{:else}
				{mode === 'question' ? 'Submit answer' : 'Analyze'}
			{/if}
		</button>
	</div>
</div>

<style>
	.question-card {
		width: 100%;
		max-width: 560px;
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
		padding: 1.75rem;
		background: var(--color-surface);
		border: 1px solid var(--color-accent);
		border-radius: var(--radius);
	}

	.question-header {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.question-icon {
		width: 36px;
		height: 36px;
		border-radius: 50%;
		background: var(--gradient-gold-btn);
		color: #0a0a0f;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.25rem;
		font-weight: 700;
		flex-shrink: 0;
	}

	.question-icon.followup {
		background: var(--color-success, #10b981);
	}

	.question-title {
		font-size: 1.05rem;
		font-weight: 600;
		color: var(--color-text);
		margin: 0;
	}

	.question-text {
		font-size: 0.95rem;
		color: var(--color-text);
		line-height: 1.5;
		margin: 0;
	}

	.options {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.option {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.75rem 1rem;
		background: var(--color-surface-2);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		cursor: pointer;
		transition: all 0.15s;
	}

	.option:hover {
		border-color: var(--color-accent);
	}

	.option.selected {
		border-color: var(--color-accent);
		background: rgba(213, 166, 41, 0.1);
	}

	.option input[type='radio'] {
		appearance: none;
		-webkit-appearance: none;
		width: 18px;
		height: 18px;
		border: 2px solid var(--color-border);
		border-radius: 50%;
		flex-shrink: 0;
		cursor: pointer;
		position: relative;
		transition: border-color 0.15s;
	}

	.option input[type='radio']:checked {
		border-color: var(--color-accent);
	}

	.option input[type='radio']:checked::after {
		content: '';
		position: absolute;
		top: 3px;
		left: 3px;
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: var(--color-accent);
	}

	.option-text {
		font-size: 0.9rem;
		color: var(--color-text);
	}

	.custom-input {
		padding: 0.75rem 1rem;
		background: var(--color-surface-2);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		color: var(--color-text);
		font-size: 0.9rem;
		outline: none;
		transition: border-color 0.15s;
	}

	.custom-input:focus {
		border-color: var(--color-accent);
	}

	.custom-input::placeholder {
		color: var(--color-text-muted);
	}

	.custom-input:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.followup-textarea {
		min-height: 80px;
		resize: vertical;
		font-family: inherit;
	}

	.actions {
		display: flex;
		justify-content: flex-end;
	}

	.submit-btn {
		padding: 0.625rem 1.25rem;
		background: var(--gradient-gold-btn);
		color: #0a0a0f;
		border: 2px solid var(--color-gold-border);
		border-radius: var(--radius-pill);
		font-size: 0.875rem;
		font-weight: 600;
		transition: filter 0.2s;
		box-shadow: var(--gold-btn-shadow);
	}

	.submit-btn:hover:not(:disabled) {
		filter: brightness(1.15);
	}

	.submit-btn:disabled {
		opacity: 0.4;
		cursor: not-allowed;
	}
</style>
