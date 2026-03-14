export interface ProgressEvent {
	step: 'parsing' | 'analyzing' | 'generating';
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

export interface FinancialReport {
	summary: FinancialSummary;
	categories: CategoryBreakdown[];
	top_merchants: MerchantSummary[];
	insights: string[];
	monthly_trend: MonthlyTrend[];
}

export interface AnalysisResult {
	report: FinancialReport;
	podcast_script: string;
}

export interface DocumentRequest {
	document_type: string;
	reason: string;
}

export type AppState = 'idle' | 'processing' | 'awaiting_documents' | 'done' | 'error';
