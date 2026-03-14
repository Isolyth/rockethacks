<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import favicon from '$lib/assets/favicon.svg';
	import { auth, clearAuth, hydrateAuth, isAuthenticated } from '$lib/stores/auth.svelte';
	import { onMount } from 'svelte';
	import '../app.css';

	let { children } = $props();

	onMount(() => {
		hydrateAuth();
	});

	function handleLogout() {
		clearAuth();
		goto('/');
	}

	let currentPath = $derived($page.url.pathname as string);
	let showNav = $derived(!auth.loading);
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

{#if showNav}
	<header class="app-header">
		<div class="header-content">
			<a href="/" class="logo"><img src="/logo.svg" alt="Easy MonAI" /></a>
			<nav class="nav-links">
				{#if isAuthenticated()}
					<a href="/dashboard" class="nav-link" class:active={currentPath === '/dashboard'}
						>Dashboard</a
					>
					<a href="/analyze" class="nav-link" class:active={currentPath.startsWith('/analyze')}
						>New Analysis</a
					>
					<span class="user-name">{auth.user?.display_name}</span>
					<button class="nav-btn" onclick={handleLogout}>Log Out</button>
				{:else if currentPath !== '/'}
					<a href="/login" class="nav-link">Log In</a>
				{/if}
			</nav>
		</div>
	</header>
{/if}

{@render children()}

<style>
	.app-header {
		position: sticky;
		top: 0;
		width: 100%;
		background: rgba(10, 10, 10, 0.85);
		backdrop-filter: blur(12px);
		-webkit-backdrop-filter: blur(12px);
		border-bottom: 1px solid var(--color-border);
		z-index: 100;
	}

	.header-content {
		max-width: 1400px;
		margin: 0 auto;
		padding: 0.75rem 1.5rem;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.logo {
		display: flex;
		align-items: center;
		text-decoration: none;
	}

	.logo img {
		height: 36px;
		width: auto;
	}

	.nav-links {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.nav-link {
		color: var(--color-text-muted);
		text-decoration: none;
		font-size: 0.875rem;
		padding: 0.4rem 0.75rem;
		border-radius: var(--radius-pill);
		transition: all 0.2s;
	}

	.nav-link:hover,
	.nav-link.active {
		color: var(--color-text);
		background: var(--color-surface-2);
	}

	.user-name {
		font-size: 0.875rem;
		color: var(--color-text-muted);
	}

	.nav-btn {
		padding: 0.4rem 0.75rem;
		background: transparent;
		color: var(--color-text-muted);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-pill);
		font-size: 0.875rem;
		cursor: pointer;
		transition: all 0.2s;
	}

	.nav-btn:hover {
		border-color: var(--color-accent);
		color: var(--color-text);
	}
</style>
