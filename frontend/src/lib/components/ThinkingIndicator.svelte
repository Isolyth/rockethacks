<script lang="ts">
	let { text }: { text: string } = $props();

	// Extract the first markdown bold header (e.g. "**Analyzing income**")
	let header = $derived(() => {
		const match = text.match(/\*\*(.+?)\*\*/);
		return match ? match[1] : text.split('\n')[0].trim();
	});
</script>

<div class="thinking">
	<div class="thinking-dot"></div>
	<span class="thinking-label">{header()}</span>
</div>

<style>
	.thinking {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
	}

	.thinking-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: var(--color-primary);
		animation: pulse 1.5s ease-in-out infinite;
	}

	@keyframes pulse {
		0%,
		100% {
			opacity: 0.4;
		}
		50% {
			opacity: 1;
		}
	}

	.thinking-label {
		font-size: 0.85rem;
		color: var(--color-text-muted);
		font-weight: 500;
	}
</style>
