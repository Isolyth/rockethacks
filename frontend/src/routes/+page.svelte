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
		<div class="hero-inner">
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
					onclick={() => goto("/login")}
					type="button">Log In</button
				>
			</div>
		</div>
	</section>

	<!-- Features -->
	<section class="features">
		<h2>What you get</h2>
		<div class="feature-grid">
			<div class="feature-card">
				<div class="feature-icon">
					<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
						<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
						<polyline points="14 2 14 8 20 8" />
						<line x1="16" y1="13" x2="8" y2="13" />
						<line x1="16" y1="17" x2="8" y2="17" />
						<polyline points="10 9 9 9 8 9" />
					</svg>
				</div>
				<h3>Smart Parsing</h3>
				<p>Upload PDF or CSV bank statements. Our AI reads and categorizes every transaction automatically.</p>
			</div>
			<div class="feature-card">
				<div class="feature-icon">
					<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
						<line x1="18" y1="20" x2="18" y2="10" />
						<line x1="12" y1="20" x2="12" y2="4" />
						<line x1="6" y1="20" x2="6" y2="14" />
					</svg>
				</div>
				<h3>Detailed Reports</h3>
				<p>Get income vs. expenses, category breakdowns, top merchants, and actionable financial insights.</p>
			</div>
			<div class="feature-card">
				<div class="feature-icon">
					<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
						<path d="M9 18V5l12-2v13" />
						<circle cx="6" cy="18" r="3" />
						<circle cx="18" cy="16" r="3" />
					</svg>
				</div>
				<h3>AI Podcast</h3>
				<p>Listen to a personalized narration of your finances, complete with highlights and recommendations.</p>
			</div>
			<div class="feature-card">
				<div class="feature-icon">
					<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
						<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
					</svg>
				</div>
				<h3>Advisor Chat</h3>
				<p>Ask follow-up "what-if" questions and get AI-powered financial advice based on your data.</p>
			</div>
		</div>
	</section>

	<!-- How it works -->
	<section class="how-it-works">
		<h2>How it works</h2>
		<div class="steps">
			<div class="step">
				<span class="step-number">1</span>
				<h3>Upload</h3>
				<p>Drop in your bank statement PDFs or CSVs</p>
			</div>
			<div class="step-arrow">
				<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<line x1="5" y1="12" x2="19" y2="12" />
					<polyline points="12 5 19 12 12 19" />
				</svg>
			</div>
			<div class="step">
				<span class="step-number">2</span>
				<h3>Analyze</h3>
				<p>AI parses, categorizes, and generates your report</p>
			</div>
			<div class="step-arrow">
				<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<line x1="5" y1="12" x2="19" y2="12" />
					<polyline points="12 5 19 12 12 19" />
				</svg>
			</div>
			<div class="step">
				<span class="step-number">3</span>
				<h3>Listen & Explore</h3>
				<p>Get your podcast, review insights, and chat with your advisor</p>
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
		padding: 5rem 1.5rem 4rem;
		text-align: center;
		display: flex;
		justify-content: center;
	}

	.hero-inner {
		max-width: 680px;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 1.5rem;
	}

	.hero-logo {
		height: 90px;
		width: auto;
	}

	h1 {
		font-size: 2.25rem;
		font-weight: 700;
		line-height: 1.15;
		background: var(--gradient-gold);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
	}

	.hero-sub {
		font-size: 1.1rem;
		color: var(--color-text-muted);
		line-height: 1.6;
		max-width: 540px;
	}

	.hero-actions {
		display: flex;
		gap: 1rem;
		margin-top: 0.5rem;
	}

	.primary-btn {
		padding: 0.875rem 1.75rem;
		background: var(--gradient-gold-btn);
		color: #0a0a0f;
		border: 2px solid var(--color-gold-border);
		border-radius: var(--radius-pill);
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		transition: filter 0.2s;
		box-shadow: var(--gold-btn-shadow);
	}

	.primary-btn:hover {
		filter: brightness(1.15);
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
		transition: all 0.2s;
	}

	.ghost-btn:hover {
		background: var(--color-surface-2);
		border-color: var(--color-accent);
	}

	/* Features */
	.features {
		padding: 4rem 1.5rem;
		max-width: 1000px;
		margin: 0 auto;
		width: 100%;
	}

	.features h2,
	.how-it-works h2,
	.languages-section h2,
	.cta h2 {
		text-align: center;
		font-size: 1.5rem;
		font-weight: 700;
		margin-bottom: 2rem;
	}

	.feature-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
		gap: 1.5rem;
	}

	.feature-card {
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		padding: 1.5rem;
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.feature-icon {
		color: var(--color-accent);
	}

	.feature-card h3 {
		font-size: 1.05rem;
		font-weight: 600;
	}

	.feature-card p {
		font-size: 0.9rem;
		color: var(--color-text-muted);
		line-height: 1.5;
	}

	/* How it works */
	.how-it-works {
		padding: 4rem 1.5rem;
		max-width: 800px;
		margin: 0 auto;
		width: 100%;
	}

	.steps {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 1.5rem;
	}

	.step {
		text-align: center;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
		flex: 1;
	}

	.step-number {
		width: 40px;
		height: 40px;
		border-radius: 50%;
		background: var(--gradient-gold-btn);
		border: 2px solid var(--color-gold-border);
		color: #0a0a0f;
		display: flex;
		align-items: center;
		justify-content: center;
		font-weight: 700;
		font-size: 1.1rem;
		box-shadow: var(--gold-btn-shadow);
	}

	.step h3 {
		font-size: 1rem;
		font-weight: 600;
	}

	.step p {
		font-size: 0.85rem;
		color: var(--color-text-muted);
		line-height: 1.4;
	}

	.step-arrow {
		color: var(--color-text-muted);
		flex-shrink: 0;
		margin-top: -2rem;
	}

	/* Languages */
	.languages-section {
		padding: 3rem 1.5rem;
		text-align: center;
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
	}

	.landing-footer p {
		font-size: 0.8rem;
		color: var(--color-text-muted);
	}

	/* Responsive */
	@media (max-width: 600px) {
		h1 {
			font-size: 1.65rem;
		}

		.hero-actions {
			flex-direction: column;
			width: 100%;
		}

		.hero-actions > button {
			width: 100%;
		}

		.steps {
			flex-direction: column;
		}

		.step-arrow {
			transform: rotate(90deg);
			margin-top: 0;
		}
	}
</style>
