<script lang="ts">
	import DOMPurify from 'isomorphic-dompurify';
	import { marked } from 'marked';
	import type { FinancialReport } from '$lib/types';
	import { streamFollowup } from '$lib/api';
	import { auth } from '$lib/stores/auth.svelte';

	let { report, language = 'en' }: { report: FinancialReport; language?: string } = $props();

	let chatHistory = $state<{ role: 'user' | 'model'; content: string }[]>([]);
	let chatInput = $state('');
	let isStreaming = $state(false);
	let streamingText = $state('');
	let error = $state<string | null>(null);
	let chatLog = $state<HTMLDivElement | null>(null);

	const THINKING_HEADERS = [
		'Analyzing your question',
		'Reviewing the numbers',
		'Running projections',
		'Crunching the data',
		'Thinking it through'
	];
	let thinkingIndex = $state(0);
	let showThinking = $derived(isStreaming && !streamingText);

	$effect(() => {
		if (!showThinking) return;
		const id = setInterval(() => {
			thinkingIndex++;
		}, 3000);
		return () => clearInterval(id);
	});

	let thinkingLabel = $derived(THINKING_HEADERS[thinkingIndex % THINKING_HEADERS.length]);

	function renderMarkdown(text: string): string {
		const raw = marked.parse(text, { async: false }) as string;
		return DOMPurify.sanitize(raw);
	}

	function scrollToBottom() {
		if (chatLog) {
			requestAnimationFrame(() => {
				chatLog!.scrollTop = chatLog!.scrollHeight;
			});
		}
	}

	async function submitChat() {
		const prompt = chatInput.trim();
		if (!prompt || isStreaming) return;

		error = null;
		isStreaming = true;
		streamingText = '';
		thinkingIndex = 0;

		chatHistory = [...chatHistory, { role: 'user', content: prompt }];
		chatInput = '';
		scrollToBottom();

		try {
			await streamFollowup(auth.token, report, prompt, chatHistory, language, {
				onChunk: (text) => {
					streamingText += text;
					scrollToBottom();
				},
				onDone: (fullText) => {
					chatHistory = [...chatHistory, { role: 'model', content: fullText }];
					streamingText = '';
					isStreaming = false;
					scrollToBottom();
				},
				onError: (msg) => {
					error = msg;
					isStreaming = false;
				}
			});
		} catch (err: any) {
			error = err.message || 'Something went wrong';
			isStreaming = false;
		}
	}
</script>

<div class="advisor-chat">
	<h3>Advisor Chat</h3>
	<p class="chat-subtitle">Ask follow-up questions about your financial report.</p>

	{#if chatHistory.length > 0 || isStreaming}
		<div class="chat-log" bind:this={chatLog}>
			{#each chatHistory as msg}
				<div class="chat-bubble {msg.role}">
					{#if msg.role === 'model'}
						<div class="msg-content markdown">{@html renderMarkdown(msg.content)}</div>
					{:else}
						<div class="msg-content">{msg.content}</div>
					{/if}
				</div>
			{/each}
			{#if isStreaming}
				{#if streamingText}
					<div class="chat-bubble model">
						<div class="msg-content markdown">{@html renderMarkdown(streamingText)}</div>
					</div>
				{:else}
					<div class="thinking">
						<div class="thinking-dot"></div>
						<span class="thinking-label">{thinkingLabel}</span>
					</div>
				{/if}
			{/if}
		</div>
	{/if}

	{#if error}
		<p class="error">{error}</p>
	{/if}

	<div class="chat-input-wrapper">
		<textarea
			class="chat-input"
			placeholder="e.g., What if I cut my dining spending in half?"
			bind:value={chatInput}
			disabled={isStreaming}
			onkeydown={(e) => {
				if (e.key === 'Enter' && !e.shiftKey && chatInput.trim() && !isStreaming) {
					e.preventDefault();
					submitChat();
				}
			}}
		></textarea>
		<button class="send-btn" disabled={isStreaming || !chatInput.trim()} onclick={submitChat}>
			{isStreaming ? '...' : 'Ask'}
		</button>
	</div>
</div>

<style>
	.advisor-chat {
		width: 100%;
		background: var(--color-surface);
		backdrop-filter: blur(12px);
		-webkit-backdrop-filter: blur(12px);
		border-radius: var(--radius);
		border: 1px solid var(--color-border);
		padding: 1.5rem;
		display: flex;
		flex-direction: column;
	}

	h3 {
		font-size: 1.1rem;
		margin: 0 0 0.25rem;
	}

	.chat-subtitle {
		color: var(--color-text-muted);
		margin: 0 0 1rem;
		font-size: 0.875rem;
	}

	.chat-log {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
		margin-bottom: 1rem;
		max-height: 400px;
		overflow-y: auto;
		padding-right: 0.5rem;
	}

	.chat-bubble {
		max-width: 85%;
		padding: 0.75rem 1rem;
		border-radius: 12px;
		line-height: 1.5;
		font-size: 0.9rem;
	}

	.chat-bubble.user {
		align-self: flex-end;
		background: var(--color-accent);
		color: #0a0a0f;
		border-bottom-right-radius: 4px;
	}

	.chat-bubble.model {
		align-self: flex-start;
		background: var(--color-surface-2, rgba(255, 255, 255, 0.05));
		color: var(--color-text);
		border: 1px solid var(--color-border);
		border-bottom-left-radius: 4px;
	}

	.msg-content.markdown :global(p) {
		margin: 0 0 0.5rem;
	}

	.msg-content.markdown :global(p:last-child) {
		margin: 0;
	}

	.msg-content.markdown :global(ul),
	.msg-content.markdown :global(ol) {
		margin: 0.25rem 0;
		padding-left: 1.25rem;
	}

	.msg-content.markdown :global(li) {
		margin-bottom: 0.25rem;
	}

	.msg-content.markdown :global(strong) {
		font-weight: 600;
	}

	.msg-content.markdown :global(code) {
		background: rgba(0, 0, 0, 0.2);
		padding: 0.1rem 0.3rem;
		border-radius: 3px;
		font-size: 0.85em;
	}

	.thinking {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.75rem 0;
	}

	.thinking-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: var(--color-accent);
		animation: pulse 1.5s ease-in-out infinite;
	}

	.thinking-label {
		font-size: 0.85rem;
		color: var(--color-text-muted);
		font-weight: 500;
	}

	@keyframes pulse {
		0%, 100% { opacity: 0.4; }
		50% { opacity: 1; }
	}

	.error {
		color: var(--color-danger);
		font-size: 0.85rem;
		margin: 0 0 0.75rem;
	}

	.chat-input-wrapper {
		display: flex;
		gap: 0.5rem;
		align-items: flex-end;
	}

	.chat-input {
		flex: 1;
		min-height: 48px;
		max-height: 120px;
		resize: vertical;
		padding: 0.625rem 0.75rem;
		border-radius: var(--radius-sm);
		border: 1px solid var(--color-border);
		background: var(--color-bg);
		color: var(--color-text);
		font-family: inherit;
		font-size: 0.9rem;
	}

	.chat-input:focus {
		outline: none;
		border-color: var(--color-accent);
	}

	.chat-input:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.send-btn {
		background: var(--gradient-gold-btn);
		color: #0a0a0f;
		border: 2px solid var(--color-gold-border);
		border-radius: var(--radius-pill);
		padding: 0 1.25rem;
		height: 48px;
		font-weight: 600;
		cursor: pointer;
		transition: filter 0.2s;
		font-size: 0.9rem;
		box-shadow: var(--gold-btn-shadow);
	}

	.send-btn:hover:not(:disabled) {
		filter: brightness(1.15);
	}

	.send-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
</style>
