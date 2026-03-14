"""Shared fixtures for backend tests."""

import pytest


VALID_REPORT_DATA = {
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
        {"name": "Amazon", "total": 350.0, "count": 5},
    ],
    "insights": ["You spend 25% on food", "Transportation costs are moderate"],
    "monthly_trend": [
        {"month": "2024-01", "income": 5000.0, "expenses": 3200.0},
    ],
}

VALID_GROUNDING_DATA = {
    "sources": [
        {"uri": "https://example.com/savings", "title": "Savings Rates 2024", "domain": "example.com"},
        {"uri": "https://example.com/spending", "title": "Average Spending", "domain": "example.com"},
    ],
    "citations": [
        {"text_segment": "The average savings rate is 20%", "source_indices": [0]},
    ],
    "search_entry_point_html": "<div class='search-chip'>Powered by Google</div>",
}

MOCK_PODCAST_SCRIPT = "Welcome to your financial podcast! Let's dive into your spending habits."

SAMPLE_CSV = b"date,amount,description\n2024-01-01,50.00,Coffee Shop\n2024-01-02,120.00,Grocery Store"


@pytest.fixture
def valid_report_data():
    """Return a deep copy of valid report data for tests that modify it."""
    import copy
    return copy.deepcopy(VALID_REPORT_DATA)


@pytest.fixture
def sample_csv():
    return SAMPLE_CSV


@pytest.fixture
def mock_podcast_script():
    return MOCK_PODCAST_SCRIPT
