<script lang="ts">
	let { script }: { script: string } = $props();
	let copied = $state(false);

	async function copyToClipboard() {
		await navigator.clipboard.writeText(script);
		copied = true;
		setTimeout(() => (copied = false), 2000);
	}
</script>

<div class="podcast">
	<div class="podcast-header">
		<h3>Podcast Script</h3>
		<button class="copy-btn" onclick={copyToClipboard} type="button">
			{copied ? 'Copied!' : 'Copy'}
		</button>
	</div>

	<div class="script-body">
		{#each script.split('\n\n') as paragraph}
			<p>{paragraph}</p>
		{/each}
	</div>
</div>

<style>
	.podcast {
		width: 100%;
		max-width: 700px;
	}

	.podcast-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}

	h3 {
		font-size: 1.1rem;
	}

	.copy-btn {
		padding: 0.4rem 1rem;
		background: var(--color-surface-2);
		color: var(--color-text-muted);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		font-size: 0.8rem;
		transition: all 0.2s;
	}

	.copy-btn:hover {
		background: var(--color-primary);
		color: white;
		border-color: var(--color-primary);
	}

	.script-body {
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		padding: 1.5rem;
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.script-body p {
		font-size: 0.925rem;
		line-height: 1.7;
		color: var(--color-text);
	}
</style>
