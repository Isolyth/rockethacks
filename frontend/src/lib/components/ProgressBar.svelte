<script lang="ts">
	import type { ProgressEvent } from '$lib/types';

	let { progress }: { progress: ProgressEvent } = $props();

	const steps = ['parsing', 'analyzing', 'generating', 'narrating'] as const;
	const stepLabels = {
		parsing: 'Parsing',
		analyzing: 'Analyzing',
		generating: 'Generating',
		narrating: 'Narrating'
	};

	function stepIndex(step: string): number {
		return steps.indexOf(step as (typeof steps)[number]);
	}
</script>

<div class="progress-container">
	<div class="steps">
		{#each steps as step, i}
			<div
				class="step"
				class:active={step === progress.step}
				class:done={stepIndex(progress.step) > i}
			>
				<div class="step-dot">
					{#if stepIndex(progress.step) > i}
						<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
							<polyline points="20 6 9 17 4 12" />
						</svg>
					{/if}
				</div>
				<span class="step-label">{stepLabels[step]}</span>
			</div>
			{#if i < steps.length - 1}
				<div class="step-line" class:filled={stepIndex(progress.step) > i}></div>
			{/if}
		{/each}
	</div>

	<div class="bar-track">
		<div class="bar-fill" style="width: {progress.percent}%"></div>
	</div>

	<p class="status-message">{progress.message}</p>
</div>

<style>
	.progress-container {
		width: 100%;
		max-width: 560px;
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.steps {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0;
	}

	.step {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
		opacity: 0.4;
		transition: opacity 0.3s;
	}

	.step.active,
	.step.done {
		opacity: 1;
	}

	.step-dot {
		width: 32px;
		height: 32px;
		border-radius: 50%;
		border: 2px solid var(--color-border);
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--color-surface);
		transition: all 0.3s;
	}

	.step.active .step-dot {
		border-color: var(--color-primary);
		background: var(--color-primary);
		box-shadow: 0 0 12px rgba(99, 102, 241, 0.4);
	}

	.step.done .step-dot {
		border-color: var(--color-success);
		background: var(--color-success);
	}

	.step-label {
		font-size: 0.75rem;
		font-weight: 500;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.step-line {
		flex: 1;
		height: 2px;
		background: var(--color-border);
		margin: 0 0.5rem;
		margin-bottom: 1.75rem;
		min-width: 40px;
		transition: background 0.3s;
	}

	.step-line.filled {
		background: var(--color-success);
	}

	.bar-track {
		width: 100%;
		height: 8px;
		background: var(--color-surface);
		border-radius: 4px;
		overflow: hidden;
	}

	.bar-fill {
		height: 100%;
		background: linear-gradient(90deg, var(--color-primary), var(--color-primary-light));
		border-radius: 4px;
		transition: width 0.4s ease;
	}

	.status-message {
		text-align: center;
		color: var(--color-text-muted);
		font-size: 0.9rem;
	}
</style>
