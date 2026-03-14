<script lang="ts">
	import type { DocumentRequest } from '$lib/types';
	import { handleDrop as onDrop, handleFileSelect as onFileSelect, filterValidFiles, formatSize } from '$lib/utils/file-upload';

	let {
		request,
		onrespond
	}: {
		request: DocumentRequest;
		onrespond: (action: 'upload' | 'skip', files?: File[]) => void;
	} = $props();

	let files = $state<File[]>([]);
	let dragging = $state(false);
	let fileInput: HTMLInputElement;

	function addFiles(newFiles: File[]) {
		const { valid } = filterValidFiles(newFiles);
		files = [...files, ...valid];
	}

	function removeFile(index: number) {
		files = files.filter((_, i) => i !== index);
	}

	function handleDrop(e: DragEvent) {
		dragging = false;
		onDrop(e, addFiles);
	}

	function handleDragOver(e: DragEvent) {
		e.preventDefault();
		dragging = true;
	}

	function handleDragLeave() {
		dragging = false;
	}
</script>

<div class="request-card">
	<div class="request-header">
		<div class="request-icon">?</div>
		<h3 class="request-title">Additional document needed</h3>
	</div>

	<div class="request-details">
		<p class="request-type">Looking for: <strong>{request.document_type}</strong></p>
		<p class="request-reason">{request.reason}</p>
	</div>

	<button
		class="dropzone"
		class:dragging
		ondrop={handleDrop}
		ondragover={handleDragOver}
		ondragleave={handleDragLeave}
		onclick={() => fileInput.click()}
		type="button"
	>
		<svg
			width="32"
			height="32"
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			stroke-width="1.5"
		>
			<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
			<polyline points="17 8 12 3 7 8" />
			<line x1="12" y1="3" x2="12" y2="15" />
		</svg>
		<p class="dropzone-text">Drop files here or click to browse</p>
		<p class="dropzone-sub">PDF, CSV</p>
	</button>

	<input
		bind:this={fileInput}
		type="file"
		accept=".pdf,.csv"
		multiple
		onchange={(e) => onFileSelect(e, addFiles)}
		hidden
	/>

	<p class="disclosure-text">
		Note: Uploaded documents will be processed by a third-party AI service.
	</p>

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
	{/if}

	<div class="actions">
		<button class="skip-btn" onclick={() => onrespond('skip')} type="button">
			Skip — continue without
		</button>
		{#if files.length > 0}
			<button class="upload-btn" onclick={() => onrespond('upload', files)} type="button">
				Upload {files.length} {files.length === 1 ? 'file' : 'files'}
			</button>
		{/if}
	</div>
</div>

<style>
	.request-card {
		width: 100%;
		max-width: 560px;
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
		padding: 1.75rem;
		background: var(--color-surface);
		border: 1px solid var(--color-warning);
		border-radius: var(--radius);
		box-shadow: var(--shadow-inset);
	}

	.request-header {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.request-icon {
		width: 36px;
		height: 36px;
		border-radius: 50%;
		background: var(--color-warning);
		color: black;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.25rem;
		font-weight: 700;
		flex-shrink: 0;
	}

	.request-title {
		font-size: 1.05rem;
		font-weight: 600;
		color: var(--color-text);
		margin: 0;
	}

	.request-details {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.request-type {
		font-size: 0.95rem;
		color: var(--color-text);
		margin: 0;
	}

	.request-reason {
		font-size: 0.9rem;
		color: var(--color-text-muted);
		line-height: 1.5;
		margin: 0;
	}

	.dropzone {
		border: 2px dashed var(--color-border);
		border-radius: var(--radius-sm);
		padding: 1.5rem 1rem;
		text-align: center;
		background: var(--color-surface-2);
		transition: all 0.2s ease;
		color: var(--color-text-muted);
		width: 100%;
		font-size: inherit;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
	}

	.dropzone:hover,
	.dropzone.dragging {
		border-color: var(--color-warning);
		color: var(--color-text);
	}

	.dropzone-text {
		font-size: 0.9rem;
		margin: 0;
	}

	.dropzone-sub {
		font-size: 0.8rem;
		opacity: 0.6;
		margin: 0;
	}

	.disclosure-text {
		font-size: 0.8rem;
		color: var(--color-text-muted);
		text-align: center;
		margin-top: -0.75rem;
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
		padding: 0.6rem 0.75rem;
		background: var(--color-surface-2);
		border-radius: var(--radius-sm);
		border: 1px solid var(--color-border);
	}

	.file-icon {
		font-size: 1.1rem;
	}

	.file-name {
		flex: 1;
		font-size: 0.85rem;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.file-size {
		font-size: 0.75rem;
		color: var(--color-text-muted);
	}

	.file-remove {
		background: none;
		border: none;
		color: var(--color-text-muted);
		font-size: 1.1rem;
		padding: 0 0.25rem;
		line-height: 1;
	}

	.file-remove:hover {
		color: var(--color-danger);
	}

	.actions {
		display: flex;
		gap: 0.75rem;
		justify-content: flex-end;
	}

	.skip-btn {
		padding: 0.625rem 1.25rem;
		background: var(--color-surface-2);
		color: var(--color-text-muted);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		font-size: 0.875rem;
		transition: all 0.2s;
	}

	.skip-btn:hover {
		border-color: var(--color-text-muted);
		color: var(--color-text);
	}

	.upload-btn {
		padding: 0.625rem 1.25rem;
		background: var(--color-warning);
		color: black;
		border: none;
		border-radius: var(--radius-sm);
		font-size: 0.875rem;
		font-weight: 600;
		transition: background 0.2s;
	}

	.upload-btn:hover {
		filter: brightness(1.1);
	}
</style>
