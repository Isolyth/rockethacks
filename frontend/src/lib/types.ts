export interface ProgressEvent {
	step: 'parsing' | 'analyzing' | 'generating' | 'narrating';
	message: string;
	percent: number;
}

export interface CategoryBreakdown {
	name: string;
	total: number;
	percentage: number;
	transactions: number;
}

export interface FinancialSummary {
	total_income: number;
	total_expenses: number;
	net_savings: number;
	date_range: string;
}

export interface MerchantSummary {
	name: string;
	total: number;
	count: number;
}

export interface MonthlyTrend {
	month: string;
	income: number;
	expenses: number;
}

export interface GroundingSource {
	uri: string;
	title: string | null;
	domain: string | null;
}

export interface GroundingCitation {
	text_segment: string;
	source_indices: number[];
}

export interface GroundingData {
	sources: GroundingSource[];
	citations: GroundingCitation[];
	search_entry_point_html: string | null;
}

export interface FinancialReport {
	summary: FinancialSummary;
	categories: CategoryBreakdown[];
	top_merchants: MerchantSummary[];
	insights: string[];
	monthly_trend: MonthlyTrend[];
	grounding?: GroundingData | null;
}

export interface AnalysisResult {
	report: FinancialReport;
	podcast_script: string;
}

export interface PodcastSentence {
	text: string;
	start: number;
	end: number;
}

export interface PodcastAudio {
	podcast_script: string;
	audio_base64: string | null;
	sentences: PodcastSentence[];
}

export interface DocumentRequest {
	document_type: string;
	reason: string;
}

export interface AgentQuestion {
	question: string;
	options: string[];
}

export type AppState =
	| 'idle'
	| 'processing'
	| 'awaiting_documents'
	| 'awaiting_answer'
	| 'done'
	| 'error';

// Auth & Dashboard types

export interface UserResponse {
	id: string;
	email: string;
	display_name: string;
}

export interface AuthResponse {
	token: string;
	user: UserResponse;
}

export interface ReportSummaryItem {
	id: string;
	title: string;
	created_at: string;
	language: string;
	total_income: number;
	total_expenses: number;
	net_savings: number;
}

export interface ReportDetail {
	id: string;
	title: string;
	created_at: string;
	language: string;
	report: FinancialReport;
	podcast_script: string;
	audio_url: string | null;
	statements: { id: string; filename: string; file_type: string }[];
}

export interface StatementItem {
	id: string;
	filename: string;
	uploaded_at: string;
	file_type: string;
	file_size: number;
}
