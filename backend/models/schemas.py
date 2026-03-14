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


class FinancialReport(BaseModel):
    summary: FinancialSummary
    categories: list[CategoryBreakdown]
    top_merchants: list[MerchantSummary]
    insights: list[str]
    monthly_trend: list[MonthlyTrend]


class AnalysisResult(BaseModel):
    report: FinancialReport
    podcast_script: str
