<script lang="ts">
	let { text }: { text: string } = $props();

	const FALLBACK_HEADERS = [
		'Reviewing transactions',
		'Categorizing spending',
		'Analyzing income patterns',
		'Identifying trends',
		'Checking for anomalies',
		'Evaluating savings rate',
		'Comparing monthly patterns',
		'Assessing financial health',
		'Looking at top merchants',
		'Summarizing key insights'
	];

	let fallbackIndex = $state(0);
	let lastRealText = $state('');
	let useReal = $state(false);
	let realHeader = $state('');

	// Extract the first markdown bold header (e.g. "**Analyzing income**")
	function extractHeader(t: string): string {
		const match = t.match(/\*\*(.+?)\*\*/);
		return match ? match[1] : t.split('\n')[0].trim();
	}

	let displayHeader = $derived(useReal ? realHeader : FALLBACK_HEADERS[fallbackIndex % FALLBACK_HEADERS.length]);

	// When real text arrives, show it and reset fallback cycle
	$effect(() => {
		if (text && text !== lastRealText) {
			lastRealText = text;
			realHeader = extractHeader(text);
			useReal = true;
			// After a delay, switch back to fallbacks
			const id = setTimeout(() => {
				useReal = false;
				fallbackIndex++;
			}, 4000);
			return () => clearTimeout(id);
		}
	});

	// Cycle fallbacks on an interval
	$effect(() => {
		const id = setInterval(() => {
			if (!useReal) {
				fallbackIndex++;
			}
		}, 4000);
		return () => clearInterval(id);
	});
</script>

<div class="thinking">
	<div class="coin-container">
		<span class="dollar-sign">$</span>
	</div>
	<span class="thinking-label">{displayHeader}</span>
</div>

<style>
	.thinking {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.6rem;
	}

	.coin-container {
		perspective: 120px;
		width: 24px;
		height: 24px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.dollar-sign {
		display: inline-block;
		font-size: 1.2rem;
		font-weight: 800;
		background: var(--gradient-gold);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
		animation: coinSpin 1.6s cubic-bezier(0.4, 0, 0.2, 1) infinite;
		transform-style: preserve-3d;
		backface-visibility: visible;
	}

	.thinking-label {
		font-size: 0.85rem;
		color: var(--color-text-muted);
		font-weight: 500;
	}
</style>
