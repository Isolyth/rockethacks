/**
 * Shared file upload utilities used by FileUpload and DocumentRequest components.
 */

export function handleDrop(e: DragEvent, addFiles: (files: File[]) => void): void {
	e.preventDefault();
	if (e.dataTransfer?.files) {
		addFiles(Array.from(e.dataTransfer.files));
	}
}

export function handleFileSelect(e: Event, addFiles: (files: File[]) => void): void {
	const input = e.target as HTMLInputElement;
	if (input.files) {
		addFiles(Array.from(input.files));
		input.value = '';
	}
}

const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10 MB

export function filterValidFiles(newFiles: File[]): { valid: File[]; rejected: string[] } {
	const valid: File[] = [];
	const rejected: string[] = [];
	for (const f of newFiles) {
		const ext = f.name.toLowerCase();
		if (!ext.endsWith('.pdf') && !ext.endsWith('.csv')) {
			rejected.push(`${f.name}: unsupported file type`);
		} else if (f.size > MAX_FILE_SIZE_BYTES) {
			rejected.push(`${f.name}: exceeds 10 MB limit`);
		} else {
			valid.push(f);
		}
	}
	return { valid, rejected };
}

export function formatSize(bytes: number): string {
	if (bytes < 1024) return bytes + ' B';
	if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
	return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}
