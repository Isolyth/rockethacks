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

export function filterValidFiles(newFiles: File[]): File[] {
	return newFiles.filter(
		(f) => f.name.toLowerCase().endsWith('.pdf') || f.name.toLowerCase().endsWith('.csv')
	);
}

export function formatSize(bytes: number): string {
	if (bytes < 1024) return bytes + ' B';
	if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
	return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}
