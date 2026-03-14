import pytest
from pydantic import ValidationError
from models.schemas import FinancialReport, FinancialSummary, CategoryBreakdown, MerchantSummary, MonthlyTrend


VALID_REPORT = {
    "summary": {
        "total_income": 5000.0,
        "total_expenses": 3200.0,
        "net_savings": 1800.0,
        "date_range": "2024-01-01 to 2024-01-31",
    },
    "categories": [
        {"name": "Food & Dining", "total": 800.0, "percentage": 25.0, "transactions": 15},
        {"name": "Transportation", "total": 400.0, "percentage": 12.5, "transactions": 8},
    ],
    "top_merchants": [
        {"name": "Starbucks", "total": 120.0, "count": 10},
    ],
    "insights": ["You spend 25% on food", "Transportation costs are moderate"],
    "monthly_trend": [
        {"month": "2024-01", "income": 5000.0, "expenses": 3200.0},
    ],
}


def test_valid_report():
    report = FinancialReport(**VALID_REPORT)
    assert report.summary.total_income == 5000.0
    assert len(report.categories) == 2
    assert report.categories[0].name == "Food & Dining"
    assert len(report.top_merchants) == 1
    assert len(report.insights) == 2


def test_report_missing_summary():
    data = {**VALID_REPORT}
    del data["summary"]
    with pytest.raises(ValidationError):
        FinancialReport(**data)


def test_report_missing_categories():
    data = {**VALID_REPORT}
    del data["categories"]
    with pytest.raises(ValidationError):
        FinancialReport(**data)


def test_report_bad_category_type():
    data = {**VALID_REPORT, "categories": [{"name": "Food", "total": "not_a_number", "percentage": 25.0, "transactions": 5}]}
    with pytest.raises(ValidationError):
        FinancialReport(**data)


def test_report_empty_lists():
    data = {
        **VALID_REPORT,
        "categories": [],
        "top_merchants": [],
        "insights": [],
        "monthly_trend": [],
    }
    report = FinancialReport(**data)
    assert report.categories == []
    assert report.top_merchants == []


def test_model_dump_roundtrip():
    report = FinancialReport(**VALID_REPORT)
    dumped = report.model_dump()
    report2 = FinancialReport(**dumped)
    assert report == report2
