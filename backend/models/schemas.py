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


# --- Auth & Dashboard models ---

class SignupRequest(BaseModel):
    email: str
    password: str
    display_name: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str


class AuthResponse(BaseModel):
    token: str
    user: UserResponse
    encryption_key: str | None = None


class ReportSummaryItem(BaseModel):
    id: str
    title: str
    created_at: str
    language: str
    total_income: float
    total_expenses: float
    net_savings: float


class ReportDetail(BaseModel):
    id: str
    title: str
    created_at: str
    language: str
    report: FinancialReport
    podcast_script: str
    audio_url: str | None = None
    sentences: list[dict] = []
    statements: list[dict] = []


class StatementItem(BaseModel):
    id: str
    filename: str
    uploaded_at: str
    file_type: str
    file_size: int
