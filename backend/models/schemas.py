from pydantic import BaseModel


class CategoryBreakdown(BaseModel):
    name: str
    total: float
    percentage: float
    transactions: int


class MerchantSummary(BaseModel):
    name: str
    total: float
    count: int


class MonthlyTrend(BaseModel):
    month: str
    income: float
    expenses: float


class FinancialSummary(BaseModel):
    total_income: float
    total_expenses: float
    net_savings: float
    date_range: str


class GroundingSource(BaseModel):
    uri: str
    title: str | None = None
    domain: str | None = None


class GroundingCitation(BaseModel):
    text_segment: str
    source_indices: list[int]


class GroundingData(BaseModel):
    sources: list[GroundingSource]
    citations: list[GroundingCitation]
    search_entry_point_html: str | None = None


class FinancialReport(BaseModel):
    summary: FinancialSummary
    categories: list[CategoryBreakdown]
    top_merchants: list[MerchantSummary]
    insights: list[str]
    monthly_trend: list[MonthlyTrend]
    grounding: GroundingData | None = None


class AnalysisResult(BaseModel):
    report: FinancialReport
    podcast_script: str


class DocumentRequest(BaseModel):
    document_type: str
    reason: str
