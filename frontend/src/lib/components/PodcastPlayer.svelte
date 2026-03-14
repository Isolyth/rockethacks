<script lang="ts">
	import type { PodcastSentence } from '$lib/types';

	let {
		podcastScript,
		audioBase64,
		sentences,
		audioUrl: externalAudioUrl = null
	}: {
		podcastScript: string;
		audioBase64: string | null;
		sentences: PodcastSentence[];
		audioUrl?: string | null;
	} = $props();

	let audioEl = $state<HTMLAudioElement | null>(null);
	let scrollContainer = $state<HTMLDivElement | null>(null);
	let currentIndex = $state(-1);
	let isPlaying = $state(false);
	let currentTime = $state(0);
	let duration = $state(0);

	let hasAudio = $derived(
		(!!audioBase64 && sentences.length > 0) || !!externalAudioUrl
	);

	// Build audio blob URL from base64, or use external URL
	let resolvedAudioUrl = $state('');

	$effect(() => {
		if (externalAudioUrl) {
			resolvedAudioUrl = externalAudioUrl;
			return;
		}
		if (!audioBase64) {
			resolvedAudioUrl = '';
			return;
		}
		const binary = atob(audioBase64);
		const bytes = new Uint8Array(binary.length);
		for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
		const blob = new Blob([bytes], { type: 'audio/mpeg' });
		const url = URL.createObjectURL(blob);
		resolvedAudioUrl = url;
		return () => URL.revokeObjectURL(url);
	});

	function onTimeUpdate() {
		if (!audioEl) return;
		currentTime = audioEl.currentTime;

		const idx = sentences.findIndex(
			(s, i) =>
				currentTime >= s.start &&
				(i === sentences.length - 1 || currentTime < sentences[i + 1].start)
		);

		if (idx !== currentIndex && idx >= 0) {
			currentIndex = idx;
			const el = document.getElementById(`sentence-${idx}`);
			if (el && scrollContainer) {
				el.scrollIntoView({ behavior: 'smooth', block: 'center' });
			}
		}
	}

	function togglePlay() {
		if (!audioEl) return;
		if (isPlaying) {
			audioEl.pause();
		} else {
			audioEl.play();
		}
	}

	function seek(e: Event) {
		if (!audioEl) return;
		const value = parseFloat((e.target as HTMLInputElement).value);
		audioEl.currentTime = value;
	}

	function clickSentence(idx: number) {
		if (!audioEl || !hasAudio) return;
		audioEl.currentTime = sentences[idx].start;
		if (!isPlaying) audioEl.play();
	}

	function formatTime(s: number): string {
		const m = Math.floor(s / 60);
		const sec = Math.floor(s % 60);
		return `${m}:${sec.toString().padStart(2, '0')}`;
	}

	function downloadMp3() {
		if (!resolvedAudioUrl) return;

		if (resolvedAudioUrl.startsWith('blob:')) {
			// Local blob URL (from base64) — download attribute works same-origin
			const a = document.createElement('a');
			a.href = resolvedAudioUrl;
			a.download = 'podcast.mp3';
			a.click();
		} else {
			// External presigned S3 URL — has Content-Disposition: attachment,
			// so navigating to it triggers a download, not a page change
			window.location.href = resolvedAudioUrl;
		}
	}

	// Fallback: split by paragraphs when no sentence data
	let paragraphs = $derived(podcastScript.split('\n\n').filter((p) => p.trim()));
</script>

<div class="podcast-player">
	<h3>Podcast</h3>

	<!-- Script text with highlighting -->
	<div class="script-scroll" bind:this={scrollContainer}>
		{#if hasAudio && sentences.length > 0}
			<div class="script-text">
				{#each sentences as sentence, i}
					<span
						id="sentence-{i}"
						class="sentence"
						class:active={i === currentIndex}
						class:past={i < currentIndex}
						onclick={() => clickSentence(i)}
						role="button"
						tabindex="0"
						onkeydown={(e) => (e.key === 'Enter' || e.key === ' ') && (e.preventDefault(), clickSentence(i))}
					>
						{sentence.text}{' '}
					</span>
				{/each}
			</div>
		{:else}
			<div class="script-text">
				{#each paragraphs as paragraph}
					<p>{paragraph}</p>
				{/each}
			</div>
		{/if}
	</div>

	<!-- Audio player -->
	{#if hasAudio}
		<div class="player">
			<audio
				bind:this={audioEl}
				src={resolvedAudioUrl}
				ontimeupdate={onTimeUpdate}
				onplay={() => (isPlaying = true)}
				onpause={() => (isPlaying = false)}
				onloadedmetadata={() => {
					if (audioEl) duration = audioEl.duration;
				}}
				onended={() => {
					isPlaying = false;
					currentIndex = -1;
				}}
			></audio>

			<button class="play-btn" onclick={togglePlay} type="button">
				{#if isPlaying}
					<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
						<rect x="6" y="4" width="4" height="16" rx="1" />
						<rect x="14" y="4" width="4" height="16" rx="1" />
					</svg>
				{:else}
					<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
						<polygon points="6,4 20,12 6,20" />
					</svg>
				{/if}
			</button>

			<span class="time">{formatTime(currentTime)}</span>

			<input
				type="range"
				class="seek-bar"
				min="0"
				max={duration}
				step="0.1"
				value={currentTime}
				oninput={seek}
			/>

			<span class="time">{formatTime(duration)}</span>

			<button class="download-btn" onclick={downloadMp3} type="button" title="Download MP3">
				<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
					<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
					<polyline points="7 10 12 15 17 10" />
					<line x1="12" y1="15" x2="12" y2="3" />
				</svg>
			</button>
		</div>
	{:else}
		<div class="no-audio">
			<p>Audio unavailable — script displayed above</p>
		</div>
	{/if}
</div>

<style>
	.podcast-player {
		width: 100%;
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	h3 {
		font-size: 1.1rem;
	}

	/* ---- Scrollable script text ---- */
	.script-scroll {
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		padding: 1.5rem;
		max-height: 350px;
		overflow-y: auto;
		scroll-behavior: smooth;
	}

	.script-text {
		font-size: 0.925rem;
		line-height: 1.8;
		color: var(--color-text-muted);
	}

	.script-text p {
		margin-bottom: 1rem;
	}

	/* Sentence highlighting */
	.sentence {
		transition: color 0.2s, background 0.2s;
		border-radius: 3px;
		padding: 1px 0;
		cursor: pointer;
	}

	.sentence:hover {
		color: var(--color-text);
	}

	.sentence.active {
		color: #fff;
		background: rgba(213, 166, 41, 0.15);
	}

	.sentence.past {
		color: var(--color-text);
	}

	/* ---- Player controls ---- */
	.player {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		padding: 0.75rem 1rem;
	}

	.play-btn {
		width: 40px;
		height: 40px;
		border-radius: 50%;
		border: 2px solid var(--color-gold-border);
		background: var(--gradient-gold-btn);
		color: #0a0a0f;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
		transition: filter 0.2s;
		box-shadow: var(--gold-btn-shadow);
	}

	.play-btn:hover {
		filter: brightness(1.15);
	}

	.time {
		font-size: 0.75rem;
		color: var(--color-text-muted);
		font-variant-numeric: tabular-nums;
		min-width: 3ch;
	}

	.seek-bar {
		flex: 1;
		height: 4px;
		-webkit-appearance: none;
		appearance: none;
		background: var(--color-border);
		border-radius: 2px;
		outline: none;
	}

	.seek-bar::-webkit-slider-thumb {
		-webkit-appearance: none;
		width: 12px;
		height: 12px;
		border-radius: 50%;
		background: var(--color-accent);
		cursor: pointer;
	}

	.seek-bar::-moz-range-thumb {
		width: 12px;
		height: 12px;
		border-radius: 50%;
		background: var(--color-accent);
		cursor: pointer;
		border: none;
	}

	.download-btn {
		width: 36px;
		height: 36px;
		border-radius: 50%;
		border: 1px solid var(--color-border);
		background: transparent;
		color: var(--color-text-muted);
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
		cursor: pointer;
		transition: color 0.2s, border-color 0.2s;
	}

	.download-btn:hover {
		color: var(--color-accent);
		border-color: var(--color-accent);
	}

	.no-audio {
		text-align: center;
		padding: 1rem;
		color: var(--color-text-muted);
		font-size: 0.85rem;
	}

	/* Scrollbar styling */
	.script-scroll::-webkit-scrollbar {
		width: 6px;
	}

	.script-scroll::-webkit-scrollbar-track {
		background: transparent;
	}

	.script-scroll::-webkit-scrollbar-thumb {
		background: var(--color-border);
		border-radius: 3px;
	}
</style>
