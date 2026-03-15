<script lang="ts">
	import { goto } from "$app/navigation";
	import { auth, isAuthenticated } from "$lib/stores/auth.svelte";

	$effect(() => {
		if (!auth.loading && isAuthenticated()) {
			goto("/dashboard");
		}
	});
</script>

<svelte:head>
	<title>Easy MonAI - AI-Powered Financial Analysis</title>
</svelte:head>

<main>
	<!-- Hero -->
	<section class="hero">
		<div class="hero-left">
			<img src="/logo.svg" alt="Easy MonAI" class="hero-logo" />
			<h1>Your financial life, analyzed and narrated by AI</h1>
			<p class="hero-sub">
				Upload your bank statements and get a detailed financial report with
				spending breakdowns, insights, and a personalized AI-narrated podcast
				— all in seconds.
			</p>
			<div class="hero-actions">
				<button
					class="primary-btn"
					onclick={() => goto("/signup")}
					type="button">Get Started Free</button
				>
				<button
					class="ghost-btn"
					onclick={() => goto("/analyze")}
					type="button">Try as Guest</button
				>
			</div>
		</div>
		<div class="hero-right">
			<div class="process-graphic">
				<!-- Step 1: Upload -->
				<div class="process-step">
					<div class="process-icon">
						<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
							<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
							<polyline points="14 2 14 8 20 8" />
							<line x1="12" y1="18" x2="12" y2="12" />
							<polyline points="9 15 12 12 15 15" />
						</svg>
					</div>
					<span class="process-label">Upload</span>
					<span class="process-detail">PDF / CSV</span>
				</div>

				<!-- Connector -->
				<div class="process-connector">
					<div class="connector-line"></div>
					<svg class="connector-arrow" width="12" height="12" viewBox="0 0 12 12" fill="none">
						<path d="M2 6h8M7 3l3 3-3 3" stroke="var(--color-accent)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
					</svg>
				</div>

				<!-- Step 2: Analyze -->
				<div class="process-step process-step-center">
					<div class="process-icon process-icon-accent">
						<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
							<circle cx="12" cy="12" r="10" />
							<path d="M12 6v6l4 2" />
						</svg>
					</div>
					<span class="process-label">AI Analyzes</span>
					<div class="process-mini-report">
						<div class="mini-bar" style="width: 85%"></div>
						<div class="mini-bar" style="width: 60%"></div>
						<div class="mini-bar" style="width: 40%"></div>
						<div class="mini-bar" style="width: 72%"></div>
					</div>
				</div>

				<!-- Connector -->
				<div class="process-connector">
					<div class="connector-line"></div>
					<svg class="connector-arrow" width="12" height="12" viewBox="0 0 12 12" fill="none">
						<path d="M2 6h8M7 3l3 3-3 3" stroke="var(--color-accent)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
					</svg>
				</div>

				<!-- Step 3: Results -->
				<div class="process-step">
					<div class="process-icon">
						<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
							<path d="M9 18V5l12-2v13" />
							<circle cx="6" cy="18" r="3" />
							<circle cx="18" cy="16" r="3" />
						</svg>
					</div>
					<span class="process-label">Report & Podcast</span>
					<span class="process-detail">Insights + Audio</span>
				</div>
			</div>
		</div>
	</section>

	<!-- How it works -->
	<section class="how-it-works">
		<h2>How it works</h2>
		<div class="steps-grid">
			<div class="step-card">
				<span class="step-number">1</span>
				<h3>Upload your statements</h3>
				<p>Drag and drop your bank statement PDFs or CSVs. Our parser handles major banks and formats automatically — no manual formatting needed.</p>
			</div>
			<div class="step-card">
				<span class="step-number">2</span>
				<h3>AI-powered analysis</h3>
				<p>Our Gemini-powered agent reads every transaction, categorizes spending, identifies trends, and may ask clarifying questions to give you the most accurate report.</p>
			</div>
			<div class="step-card">
				<span class="step-number">3</span>
				<h3>Get your report & podcast</h3>
				<p>Receive a detailed financial breakdown with income vs. expenses, top merchants, and actionable insights — plus an AI-narrated podcast you can listen to on the go.</p>
			</div>
			<div class="step-card">
				<span class="step-number">4</span>
				<h3>Chat with your advisor</h3>
				<p>Ask follow-up questions like "What if I cut dining out by 50%?" and get personalized advice based on your actual financial data.</p>
			</div>
		</div>
	</section>

	<!-- Languages -->
	<section class="languages-section">
		<h2>Available in 14 languages</h2>
		<p class="languages-sub">
			English, Spanish, French, German, Portuguese, Italian, Japanese, Korean, Chinese, Hindi, Arabic, Dutch, Polish, and Russian
		</p>
	</section>

	<!-- CTA -->
	<section class="cta">
		<h2>Ready to understand your finances?</h2>
		<p>Sign up for free and run your first analysis in under a minute.</p>
		<button
			class="primary-btn"
			onclick={() => goto("/signup")}
			type="button">Get Started</button
		>
	</section>

	<footer class="landing-footer">
		<p>Easy MonAI</p>
	</footer>
</main>

<style>
	main {
		min-height: 100vh;
		display: flex;
		flex-direction: column;
	}

	/* Hero */
	.hero {
		padding: 5rem 2rem 4rem;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 4rem;
		max-width: 1200px;
		margin: 0 auto;
		width: 100%;
		animation: fadeIn 0.6s ease;
	}

	.hero-left {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
		max-width: 520px;
	}

	.hero-right {
		flex: 1;
		display: flex;
		justify-content: center;
		max-width: 520px;
		animation: fadeInUp 0.6s ease 0.3s both;
	}

	.hero-logo {
		height: 120px;
		width: auto;
		align-self: flex-start;
		animation: fadeInUp 0.5s ease both;
	}

	h1 {
		font-size: 2.5rem;
		font-weight: 700;
		line-height: 1.12;
		background: var(--gradient-gold);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
		animation: fadeInUp 0.5s ease 0.1s both;
	}

	.hero-sub {
		font-size: 1.05rem;
		color: var(--color-text-muted);
		line-height: 1.6;
		animation: fadeInUp 0.5s ease 0.2s both;
	}

	.hero-actions {
		display: flex;
		gap: 1rem;
		margin-top: 0.5rem;
		animation: fadeInUp 0.5s ease 0.3s both;
	}

	.primary-btn {
		padding: 0.875rem 1.75rem;
		background: var(--gradient-gold-btn);
		color: #5a3a0a;
		border: 2px solid var(--color-gold-border);
		border-radius: var(--radius-pill);
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		transition: filter 0.2s;
		box-shadow: var(--gold-btn-shadow);
		position: relative;
		overflow: hidden;
	}

	.primary-btn::before {
		content: '';
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 100%;
		background: linear-gradient(
			120deg,
			transparent 0%,
			transparent 30%,
			rgba(255, 255, 255, 0.35) 50%,
			transparent 70%,
			transparent 100%
		);
		transition: none;
	}

	.primary-btn:hover {
		filter: brightness(1.1);
	}

	.primary-btn:hover::before {
		animation: goldShimmer 0.6s ease forwards;
	}

	.ghost-btn {
		padding: 0.875rem 1.75rem;
		background: transparent;
		color: var(--color-text);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-pill);
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.25s ease;
	}

	.ghost-btn:hover {
		background: var(--color-surface-2);
		border-color: var(--color-accent);
		transform: translateY(-1px);
	}

	/* Process Graphic */
	.process-graphic {
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: 12px;
		padding: 2rem 1.5rem;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.75rem;
		box-shadow: var(--shadow-inset);
		width: 100%;
		max-width: 280px;
	}

	.process-step {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.4rem;
		width: 100%;
		animation: fadeInUp 0.4s ease both;
	}

	.process-step:nth-child(1) { animation-delay: 0.4s; }
	.process-step:nth-child(3) { animation-delay: 0.6s; }
	.process-step:nth-child(5) { animation-delay: 0.8s; }

	.process-connector {
		animation: fadeIn 0.3s ease both;
	}

	.process-connector:nth-child(2) { animation-delay: 0.5s; }
	.process-connector:nth-child(4) { animation-delay: 0.7s; }

	.process-icon {
		width: 52px;
		height: 52px;
		border-radius: 12px;
		background: rgba(213, 166, 41, 0.08);
		border: 1px solid rgba(213, 166, 41, 0.2);
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--color-accent);
		transition: transform 0.25s ease, border-color 0.25s ease;
	}

	.process-step:hover .process-icon {
		transform: scale(1.08);
		border-color: var(--color-accent);
	}

	.process-icon-accent {
		background: rgba(213, 166, 41, 0.15);
		border-color: rgba(213, 166, 41, 0.35);
	}

	.process-label {
		font-size: 0.85rem;
		font-weight: 600;
		color: var(--color-text);
	}

	.process-detail {
		font-size: 0.72rem;
		color: var(--color-text-muted);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.process-connector {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0;
		height: 32px;
	}

	.connector-line {
		width: 1px;
		flex: 1;
		background: linear-gradient(180deg, rgba(213, 166, 41, 0.15), rgba(213, 166, 41, 0.4));
	}

	.connector-arrow {
		transform: rotate(90deg);
		flex-shrink: 0;
	}

	/* Mini report bars */
	.process-mini-report {
		display: flex;
		flex-direction: column;
		gap: 4px;
		width: 100%;
		max-width: 140px;
		padding-top: 0.25rem;
	}

	.mini-bar {
		height: 4px;
		border-radius: 2px;
		background: linear-gradient(90deg, var(--color-accent), var(--color-accent-light));
		opacity: 0.5;
	}

	/* How it works */
	.how-it-works {
		padding: 5rem 2rem;
		max-width: 1100px;
		margin: 0 auto;
		width: 100%;
		animation: fadeIn 0.5s ease 0.4s both;
	}

	.how-it-works h2,
	.languages-section h2,
	.cta h2 {
		text-align: center;
		font-size: 1.5rem;
		font-weight: 700;
		margin-bottom: 2.5rem;
	}

	.steps-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 1.5rem;
	}

	.step-card {
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: 8px;
		padding: 1.75rem;
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
		box-shadow: var(--shadow-inset);
		animation: fadeInUp 0.5s ease both;
		transition: transform 0.25s ease, border-color 0.25s ease;
	}

	.step-card:nth-child(1) { animation-delay: 0.5s; }
	.step-card:nth-child(2) { animation-delay: 0.6s; }
	.step-card:nth-child(3) { animation-delay: 0.7s; }
	.step-card:nth-child(4) { animation-delay: 0.8s; }

	.step-card:hover {
		transform: translateY(-3px);
		border-color: var(--color-accent);
	}

	.step-number {
		width: 36px;
		height: 36px;
		border-radius: 50%;
		background: var(--gradient-gold-btn);
		border: 2px solid var(--color-gold-border);
		color: #5a3a0a;
		display: flex;
		align-items: center;
		justify-content: center;
		font-weight: 700;
		font-size: 1rem;
		box-shadow: var(--gold-btn-shadow);
		flex-shrink: 0;
		transition: transform 0.25s ease;
	}

	.step-card:hover .step-number {
		transform: scale(1.1);
	}

	.step-card h3 {
		font-size: 1.05rem;
		font-weight: 600;
	}

	.step-card p {
		font-size: 0.9rem;
		color: var(--color-text-muted);
		line-height: 1.55;
	}

	/* Languages */
	.languages-section {
		padding: 3rem 1.5rem;
		text-align: center;
		animation: fadeIn 0.5s ease 0.6s both;
	}

	.languages-sub {
		color: var(--color-text-muted);
		font-size: 0.95rem;
		max-width: 600px;
		margin: 0 auto;
		line-height: 1.6;
	}

	/* CTA */
	.cta {
		padding: 4rem 1.5rem;
		text-align: center;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 1rem;
		animation: fadeInUp 0.5s ease 0.7s both;
	}

	.cta p {
		color: var(--color-text-muted);
		font-size: 1rem;
		margin-bottom: 0.5rem;
	}

	/* Footer */
	.landing-footer {
		text-align: center;
		padding: 2rem 1.5rem;
		border-top: 1px solid var(--color-border);
		margin-top: auto;
		animation: fadeIn 0.4s ease 0.8s both;
	}

	.landing-footer p {
		font-size: 0.8rem;
		color: var(--color-text-muted);
	}

	/* Responsive */
	@media (max-width: 900px) {
		.hero {
			flex-direction: column;
			text-align: center;
			gap: 2.5rem;
			padding: 3rem 1.5rem;
		}

		.hero-left {
			align-items: center;
			max-width: 600px;
		}

		.hero-logo {
			align-self: center;
		}

		.hero-sub {
			max-width: 500px;
		}
	}

	@media (max-width: 640px) {
		h1 {
			font-size: 1.75rem;
		}

		.hero-actions {
			flex-direction: column;
			width: 100%;
		}

		.hero-actions > button {
			width: 100%;
		}

		.steps-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
