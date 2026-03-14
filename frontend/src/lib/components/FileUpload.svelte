<script lang="ts">
	let { onupload }: { onupload: (files: File[], language: string) => void } = $props();

	const languages = [
		{ code: 'en', name: 'English' },
		{ code: 'es', name: 'Spanish' },
		{ code: 'fr', name: 'French' },
		{ code: 'de', name: 'German' },
		{ code: 'pt', name: 'Portuguese' },
		{ code: 'it', name: 'Italian' },
		{ code: 'ja', name: 'Japanese' },
		{ code: 'ko', name: 'Korean' },
		{ code: 'zh', name: 'Chinese' },
		{ code: 'hi', name: 'Hindi' },
		{ code: 'ar', name: 'Arabic' },
		{ code: 'nl', name: 'Dutch' },
		{ code: 'pl', name: 'Polish' },
		{ code: 'ru', name: 'Russian' },
	];

	let files = $state<File[]>([]);
	let selectedLanguage = $state('en');
	let dragging = $state(false);
	let fileInput: HTMLInputElement;

	function handleDrop(e: DragEvent) {
		e.preventDefault();
		dragging = false;
		if (e.dataTransfer?.files) {
			addFiles(Array.from(e.dataTransfer.files));
		}
	}

	function handleDragOver(e: DragEvent) {
		e.preventDefault();
		dragging = true;
	}

	function handleDragLeave() {
		dragging = false;
	}

	function handleFileSelect(e: Event) {
		const input = e.target as HTMLInputElement;
		if (input.files) {
			addFiles(Array.from(input.files));
			input.value = '';
		}
	}

	function addFiles(newFiles: File[]) {
		const valid = newFiles.filter(
			(f) => f.name.toLowerCase().endsWith('.pdf') || f.name.toLowerCase().endsWith('.csv')
		);
		files = [...files, ...valid];
	}

	function removeFile(index: number) {
		files = files.filter((_, i) => i !== index);
	}

	function formatSize(bytes: number): string {
		if (bytes < 1024) return bytes + ' B';
		if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
		return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
	}
</script>

<div class="upload-container">
	<button
		class="dropzone"
		class:dragging
		ondrop={handleDrop}
		ondragover={handleDragOver}
		ondragleave={handleDragLeave}
		onclick={() => fileInput.click()}
		type="button"
	>
		<div class="dropzone-icon">
			<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
				<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
				<polyline points="17 8 12 3 7 8" />
				<line x1="12" y1="3" x2="12" y2="15" />
			</svg>
		</div>
		<p class="dropzone-text">Drop your bank statements here</p>
		<p class="dropzone-sub">or click to browse &middot; PDF, CSV</p>
	</button>

	<input
		bind:this={fileInput}
		type="file"
		accept=".pdf,.csv"
		multiple
		onchange={handleFileSelect}
		hidden
	/>

	{#if files.length > 0}
		<div class="file-list">
			{#each files as file, i}
				<div class="file-item">
					<span class="file-icon">{file.name.endsWith('.pdf') ? '📄' : '📊'}</span>
					<span class="file-name">{file.name}</span>
					<span class="file-size">{formatSize(file.size)}</span>
					<button class="file-remove" onclick={() => removeFile(i)} type="button">&times;</button>
				</div>
			{/each}
		</div>

		<div class="language-row">
			<label class="language-label" for="lang-select">Report & podcast language</label>
			<select id="lang-select" class="language-select" bind:value={selectedLanguage}>
				{#each languages as lang}
					<option value={lang.code}>{lang.name}</option>
				{/each}
			</select>
		</div>

		<button class="analyze-btn" onclick={() => onupload(files, selectedLanguage)} type="button">
			Analyze {files.length} {files.length === 1 ? 'file' : 'files'}
		</button>
	{/if}
</div>

<style>
	.upload-container {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
		width: 100%;
		max-width: 560px;
	}

	.dropzone {
		border: 2px dashed var(--color-border);
		border-radius: var(--radius);
		padding: 3rem 2rem;
		text-align: center;
		background: var(--color-surface);
		transition: all 0.2s ease;
		color: var(--color-text-muted);
		width: 100%;
		font-size: inherit;
	}

	.dropzone:hover,
	.dropzone.dragging {
		border-color: var(--color-primary);
		background: var(--color-surface-2);
		color: var(--color-text);
	}

	.dropzone-icon {
		margin-bottom: 1rem;
		opacity: 0.6;
	}

	.dropzone-text {
		font-size: 1.1rem;
		font-weight: 500;
		margin-bottom: 0.25rem;
	}

	.dropzone-sub {
		font-size: 0.875rem;
		opacity: 0.7;
	}

	.file-list {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.file-item {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.75rem 1rem;
		background: var(--color-surface);
		border-radius: var(--radius-sm);
		border: 1px solid var(--color-border);
	}

	.file-icon {
		font-size: 1.25rem;
	}

	.file-name {
		flex: 1;
		font-size: 0.9rem;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.file-size {
		font-size: 0.8rem;
		color: var(--color-text-muted);
	}

	.file-remove {
		background: none;
		border: none;
		color: var(--color-text-muted);
		font-size: 1.25rem;
		padding: 0 0.25rem;
		line-height: 1;
	}

	.file-remove:hover {
		color: var(--color-danger);
	}

	.language-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
		padding: 0.75rem 1rem;
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
	}

	.language-label {
		font-size: 0.9rem;
		color: var(--color-text-muted);
	}

	.language-select {
		padding: 0.5rem 0.75rem;
		background: var(--color-surface-2);
		color: var(--color-text);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		font-size: 0.9rem;
		min-width: 140px;
	}

	.language-select:focus {
		outline: none;
		border-color: var(--color-primary);
	}

	.analyze-btn {
		padding: 0.875rem 2rem;
		background: var(--color-primary);
		color: white;
		border: none;
		border-radius: var(--radius-sm);
		font-size: 1rem;
		font-weight: 600;
		transition: background 0.2s;
	}

	.analyze-btn:hover {
		background: var(--color-primary-light);
	}
</style>
