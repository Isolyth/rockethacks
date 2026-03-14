<script lang="ts">
	import { goto } from '$app/navigation';
	import { signup } from '$lib/api';
	import { setAuth } from '$lib/stores/auth.svelte';

	let email = $state('');
	let password = $state('');
	let displayName = $state('');
	let error = $state('');
	let loading = $state(false);

	async function handleSubmit(e: Event) {
		e.preventDefault();
		error = '';
		loading = true;
		try {
			const result = await signup(email, password, displayName || undefined);
			setAuth(result.token, result.user, result.encryption_key);
			goto('/dashboard');
		} catch (err: any) {
			error = err.message || 'Signup failed';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Sign Up - Easy MonAI</title>
</svelte:head>

<main>
	<div class="auth-card">
		<h1>Sign Up</h1>
		<form onsubmit={handleSubmit}>
			<label>
				<span>Display Name (optional)</span>
				<input type="text" bind:value={displayName} placeholder="Your name" />
			</label>
			<label>
				<span>Email</span>
				<input type="email" bind:value={email} required placeholder="you@example.com" />
			</label>
			<label>
				<span>Password</span>
				<input type="password" bind:value={password} required minlength="8" placeholder="Enter password" />
				<ul class="password-requirements">
					<li class:met={password.length >= 8}>At least 8 characters</li>
					<li class:met={/[A-Z]/.test(password) && /[a-z]/.test(password)}>At least 1 uppercase & 1 lowercase letter</li>
					<li class:met={/[0-9]/.test(password)}>At least 1 number</li>
					<li class:met={/[^A-Za-z0-9]/.test(password)}>At least 1 special character</li>
				</ul>
			</label>
			{#if error}
				<p class="error">{error}</p>
			{/if}
			<button type="submit" class="submit-btn" disabled={loading}>
				{loading ? 'Creating account...' : 'Sign Up'}
			</button>
		</form>
		<p class="switch">Already have an account? <a href="/login">Log In</a></p>
	</div>
</main>

<style>
	main {
		min-height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 2rem;
	}

	.auth-card {
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		padding: 2.5rem;
		width: 100%;
		max-width: 420px;
	}

	h1 {
		margin: 0 0 1.5rem;
		font-size: 1.5rem;
		font-weight: 700;
	}

	form {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	label {
		display: flex;
		flex-direction: column;
		gap: 0.375rem;
	}

	label span {
		font-size: 0.875rem;
		color: var(--color-text-muted);
	}

	input {
		padding: 0.75rem;
		background: var(--color-bg);
		color: var(--color-text);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		font-size: 0.95rem;
	}

	input:focus {
		outline: none;
		border-color: var(--color-primary);
	}

	.error {
		color: var(--color-danger);
		font-size: 0.875rem;
		margin: 0;
	}

	.submit-btn {
		padding: 0.75rem;
		background: var(--color-primary);
		color: white;
		border: none;
		border-radius: var(--radius-sm);
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		transition: opacity 0.2s;
		margin-top: 0.5rem;
	}

	.submit-btn:hover:not(:disabled) {
		opacity: 0.9;
	}

	.submit-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.switch {
		text-align: center;
		margin-top: 1.5rem;
		font-size: 0.875rem;
		color: var(--color-text-muted);
	}

	.switch a {
		color: var(--color-primary);
		text-decoration: none;
	}

	.switch a:hover {
		text-decoration: underline;
	}

	.password-requirements {
		margin: 0.25rem 0 0;
		padding-left: 1.25rem;
		font-size: 0.75rem;
		color: var(--color-text-muted);
	}

	.password-requirements li {
		margin-bottom: 0.25rem;
		transition: color 0.2s;
	}

	.password-requirements li.met {
		color: var(--color-success, #10b981);
	}
</style>
