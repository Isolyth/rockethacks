"""Tests for models/schemas.py — Pydantic model validation."""

import pytest
from pydantic import ValidationError

from models.schemas import (
    FinancialReport,
    FinancialSummary,
    CategoryBreakdown,
    MerchantSummary,
    MonthlyTrend,
    AnalysisResult,
    DocumentRequest,
    GroundingSource,
    GroundingCitation,
    GroundingData,
)
from tests.conftest import VALID_REPORT_DATA, VALID_GROUNDING_DATA


# ── CategoryBreakdown ────────────────────────────────────────────────────────

class TestCategoryBreakdown:
    def test_valid(self):
        cat = CategoryBreakdown(name="Food", total=500.0, percentage=25.0, transactions=10)
        assert cat.name == "Food"
        assert cat.total == 500.0

    def test_zero_values(self):
        cat = CategoryBreakdown(name="Empty", total=0.0, percentage=0.0, transactions=0)
        assert cat.total == 0.0
        assert cat.transactions == 0

    def test_negative_total(self):
        # Pydantic allows negative floats by default
        cat = CategoryBreakdown(name="Refunds", total=-50.0, percentage=-5.0, transactions=2)
        assert cat.total == -50.0

    def test_missing_name(self):
        with pytest.raises(ValidationError):
            CategoryBreakdown(total=100.0, percentage=10.0, transactions=5)

    def test_missing_total(self):
        with pytest.raises(ValidationError):
            CategoryBreakdown(name="Food", percentage=10.0, transactions=5)

    def test_wrong_type_transactions(self):
        with pytest.raises(ValidationError):
            CategoryBreakdown(name="Food", total=100.0, percentage=10.0, transactions="many")

    def test_float_coercion_for_transactions(self):
        # Pydantic will coerce float to int if possible
        cat = CategoryBreakdown(name="Food", total=100.0, percentage=10.0, transactions=5.0)
        assert cat.transactions == 5


# ── MerchantSummary ──────────────────────────────────────────────────────────

class TestMerchantSummary:
    def test_valid(self):
        m = MerchantSummary(name="Starbucks", total=120.0, count=10)
        assert m.name == "Starbucks"
        assert m.count == 10

    def test_missing_name(self):
        with pytest.raises(ValidationError):
            MerchantSummary(total=120.0, count=10)

    def test_missing_count(self):
        with pytest.raises(ValidationError):
            MerchantSummary(name="Starbucks", total=120.0)

    def test_large_values(self):
        m = MerchantSummary(name="Rent LLC", total=999999.99, count=12)
        assert m.total == 999999.99


# ── MonthlyTrend ─────────────────────────────────────────────────────────────

class TestMonthlyTrend:
    def test_valid(self):
        t = MonthlyTrend(month="2024-01", income=5000.0, expenses=3000.0)
        assert t.month == "2024-01"

    def test_missing_month(self):
        with pytest.raises(ValidationError):
            MonthlyTrend(income=5000.0, expenses=3000.0)

    def test_zero_income_expenses(self):
        t = MonthlyTrend(month="2024-06", income=0.0, expenses=0.0)
        assert t.income == 0.0
        assert t.expenses == 0.0


# ── FinancialSummary ─────────────────────────────────────────────────────────

class TestFinancialSummary:
    def test_valid(self):
        s = FinancialSummary(
            total_income=5000.0, total_expenses=3200.0, net_savings=1800.0,
            date_range="2024-01-01 to 2024-01-31",
        )
        assert s.net_savings == 1800.0

    def test_missing_date_range(self):
        with pytest.raises(ValidationError):
            FinancialSummary(total_income=5000.0, total_expenses=3200.0, net_savings=1800.0)

    def test_negative_savings(self):
        s = FinancialSummary(
            total_income=2000.0, total_expenses=3000.0, net_savings=-1000.0,
            date_range="2024-01 to 2024-03",
        )
        assert s.net_savings == -1000.0

    def test_all_missing(self):
        with pytest.raises(ValidationError):
            FinancialSummary()


# ── FinancialReport ──────────────────────────────────────────────────────────

class TestFinancialReport:
    def test_valid_report(self):
        report = FinancialReport(**VALID_REPORT_DATA)
        assert report.summary.total_income == 5000.0
        assert len(report.categories) == 2
        assert report.categories[0].name == "Food & Dining"
        assert len(report.top_merchants) == 2
        assert len(report.insights) == 2

    def test_missing_summary(self, valid_report_data):
        del valid_report_data["summary"]
        with pytest.raises(ValidationError):
            FinancialReport(**valid_report_data)

    def test_missing_categories(self, valid_report_data):
        del valid_report_data["categories"]
        with pytest.raises(ValidationError):
            FinancialReport(**valid_report_data)

    def test_missing_top_merchants(self, valid_report_data):
        del valid_report_data["top_merchants"]
        with pytest.raises(ValidationError):
            FinancialReport(**valid_report_data)

    def test_missing_insights(self, valid_report_data):
        del valid_report_data["insights"]
        with pytest.raises(ValidationError):
            FinancialReport(**valid_report_data)

    def test_missing_monthly_trend(self, valid_report_data):
        del valid_report_data["monthly_trend"]
        with pytest.raises(ValidationError):
            FinancialReport(**valid_report_data)

    def test_bad_category_type(self, valid_report_data):
        valid_report_data["categories"] = [
            {"name": "Food", "total": "not_a_number", "percentage": 25.0, "transactions": 5}
        ]
        with pytest.raises(ValidationError):
            FinancialReport(**valid_report_data)

    def test_empty_lists(self, valid_report_data):
        valid_report_data["categories"] = []
        valid_report_data["top_merchants"] = []
        valid_report_data["insights"] = []
        valid_report_data["monthly_trend"] = []
        report = FinancialReport(**valid_report_data)
        assert report.categories == []
        assert report.top_merchants == []

    def test_model_dump_roundtrip(self):
        report = FinancialReport(**VALID_REPORT_DATA)
        dumped = report.model_dump()
        report2 = FinancialReport(**dumped)
        assert report == report2

    def test_model_dump_json_roundtrip(self):
        import json
        report = FinancialReport(**VALID_REPORT_DATA)
        json_str = report.model_dump_json()
        data = json.loads(json_str)
        report2 = FinancialReport(**data)
        assert report == report2

    def test_many_categories(self):
        import copy
        data = copy.deepcopy(VALID_REPORT_DATA)
        data["categories"] = [
            {"name": f"Cat{i}", "total": float(i * 100), "percentage": float(i), "transactions": i}
            for i in range(50)
        ]
        report = FinancialReport(**data)
        assert len(report.categories) == 50

    def test_extra_fields_ignored(self):
        import copy
        data = copy.deepcopy(VALID_REPORT_DATA)
        data["extra_field"] = "should be ignored"
        # Pydantic v2 ignores extra fields by default
        report = FinancialReport(**data)
        assert not hasattr(report, "extra_field")

    def test_integer_coerced_to_float(self):
        import copy
        data = copy.deepcopy(VALID_REPORT_DATA)
        data["summary"]["total_income"] = 5000  # int, not float
        report = FinancialReport(**data)
        assert report.summary.total_income == 5000.0
        assert isinstance(report.summary.total_income, float)


# ── AnalysisResult ───────────────────────────────────────────────────────────

class TestAnalysisResult:
    def test_valid(self):
        report = FinancialReport(**VALID_REPORT_DATA)
        result = AnalysisResult(report=report, podcast_script="Hello world")
        assert result.podcast_script == "Hello world"
        assert result.report.summary.total_income == 5000.0

    def test_missing_report(self):
        with pytest.raises(ValidationError):
            AnalysisResult(podcast_script="Hello")

    def test_missing_script(self):
        with pytest.raises(ValidationError):
            AnalysisResult(report=FinancialReport(**VALID_REPORT_DATA))

    def test_empty_script(self):
        result = AnalysisResult(
            report=FinancialReport(**VALID_REPORT_DATA),
            podcast_script="",
        )
        assert result.podcast_script == ""


# ── GroundingSource ──────────────────────────────────────────────────────────

class TestGroundingSource:
    def test_valid(self):
        s = GroundingSource(uri="https://example.com", title="Example", domain="example.com")
        assert s.uri == "https://example.com"

    def test_minimal(self):
        s = GroundingSource(uri="https://example.com")
        assert s.title is None
        assert s.domain is None

    def test_missing_uri(self):
        with pytest.raises(ValidationError):
            GroundingSource()


# ── GroundingCitation ───────────────────────────────────────────────────────

class TestGroundingCitation:
    def test_valid(self):
        c = GroundingCitation(text_segment="Average is 20%", source_indices=[0, 1])
        assert c.text_segment == "Average is 20%"
        assert c.source_indices == [0, 1]

    def test_empty_indices(self):
        c = GroundingCitation(text_segment="text", source_indices=[])
        assert c.source_indices == []

    def test_missing_text(self):
        with pytest.raises(ValidationError):
            GroundingCitation(source_indices=[0])


# ── GroundingData ───────────────────────────────────────────────────────────

class TestGroundingData:
    def test_valid(self):
        gd = GroundingData(**VALID_GROUNDING_DATA)
        assert len(gd.sources) == 2
        assert len(gd.citations) == 1

    def test_no_html(self):
        gd = GroundingData(sources=[], citations=[])
        assert gd.search_entry_point_html is None

    def test_empty_sources(self):
        gd = GroundingData(sources=[], citations=[], search_entry_point_html=None)
        assert gd.sources == []


# ── FinancialReport with grounding ──────────────────────────────────────────

class TestFinancialReportGrounding:
    def test_report_without_grounding(self):
        report = FinancialReport(**VALID_REPORT_DATA)
        assert report.grounding is None

    def test_report_with_grounding(self):
        import copy
        data = copy.deepcopy(VALID_REPORT_DATA)
        data["grounding"] = VALID_GROUNDING_DATA
        report = FinancialReport(**data)
        assert report.grounding is not None
        assert len(report.grounding.sources) == 2

    def test_report_grounding_roundtrip(self):
        import copy
        data = copy.deepcopy(VALID_REPORT_DATA)
        data["grounding"] = VALID_GROUNDING_DATA
        report = FinancialReport(**data)
        dumped = report.model_dump()
        report2 = FinancialReport(**dumped)
        assert report == report2


# ── DocumentRequest ──────────────────────────────────────────────────────────

class TestDocumentRequest:
    def test_valid(self):
        dr = DocumentRequest(document_type="pay stub", reason="Need income data")
        assert dr.document_type == "pay stub"
        assert dr.reason == "Need income data"

    def test_missing_document_type(self):
        with pytest.raises(ValidationError):
            DocumentRequest(reason="Need income data")

    def test_missing_reason(self):
        with pytest.raises(ValidationError):
            DocumentRequest(document_type="pay stub")

    def test_empty_strings(self):
        dr = DocumentRequest(document_type="", reason="")
        assert dr.document_type == ""
        assert dr.reason == ""
