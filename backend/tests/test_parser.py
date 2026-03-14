from services.parser import parse_csv, parse_pdf
from unittest.mock import patch, MagicMock


def test_parse_csv_decodes_bytes():
    csv_data = b"date,amount,description\n2024-01-01,50.00,Coffee Shop\n2024-01-02,120.00,Grocery Store"
    result = parse_csv(csv_data)
    assert "date,amount,description" in result
    assert "Coffee Shop" in result
    assert "Grocery Store" in result


def test_parse_csv_utf8():
    csv_data = "date,amount,description\n2024-01-01,25.00,Café".encode("utf-8")
    result = parse_csv(csv_data)
    assert "Café" in result


def test_parse_pdf_extracts_text():
    fake_page = MagicMock()
    fake_page.extract_text.return_value = "Transaction: $50.00 Coffee Shop"

    fake_reader = MagicMock()
    fake_reader.pages = [fake_page]

    with patch("services.parser.PdfReader", return_value=fake_reader):
        result = parse_pdf(b"fake pdf bytes")
        assert "Transaction: $50.00 Coffee Shop" in result


def test_parse_pdf_multiple_pages():
    page1 = MagicMock()
    page1.extract_text.return_value = "Page 1 content"
    page2 = MagicMock()
    page2.extract_text.return_value = "Page 2 content"

    fake_reader = MagicMock()
    fake_reader.pages = [page1, page2]

    with patch("services.parser.PdfReader", return_value=fake_reader):
        result = parse_pdf(b"fake pdf bytes")
        assert "Page 1 content" in result
        assert "Page 2 content" in result


def test_parse_pdf_empty_page():
    page1 = MagicMock()
    page1.extract_text.return_value = None
    page2 = MagicMock()
    page2.extract_text.return_value = "Some content"

    fake_reader = MagicMock()
    fake_reader.pages = [page1, page2]

    with patch("services.parser.PdfReader", return_value=fake_reader):
        result = parse_pdf(b"fake pdf bytes")
        assert "Some content" in result
