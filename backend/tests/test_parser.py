"""Tests for services/parser.py — PDF and CSV parsing."""

from unittest.mock import patch, MagicMock

from services.parser import parse_csv, parse_pdf


# ── CSV parsing ──────────────────────────────────────────────────────────────

class TestParseCsv:
    def test_decodes_bytes(self):
        csv_data = b"date,amount,description\n2024-01-01,50.00,Coffee Shop\n2024-01-02,120.00,Grocery Store"
        result = parse_csv(csv_data)
        assert "date,amount,description" in result
        assert "Coffee Shop" in result
        assert "Grocery Store" in result

    def test_utf8_characters(self):
        csv_data = "date,amount,description\n2024-01-01,25.00,Café".encode("utf-8")
        result = parse_csv(csv_data)
        assert "Café" in result

    def test_empty_csv(self):
        result = parse_csv(b"")
        assert result == ""

    def test_single_header_no_rows(self):
        result = parse_csv(b"date,amount,description")
        assert result == "date,amount,description"

    def test_preserves_newlines(self):
        csv_data = b"a,b\n1,2\n3,4"
        result = parse_csv(csv_data)
        assert result.count("\n") == 2

    def test_special_characters(self):
        csv_data = "col1,col2\n\"quoted, value\",normal\ntab\there,ok".encode("utf-8")
        result = parse_csv(csv_data)
        assert "quoted, value" in result
        assert "tab\there" in result

    def test_unicode_currencies(self):
        csv_data = "amount,currency\n100,\u00a5\n200,\u20ac\n300,\u00a3".encode("utf-8")
        result = parse_csv(csv_data)
        assert "\u00a5" in result  # Yen
        assert "\u20ac" in result  # Euro
        assert "\u00a3" in result  # Pound

    def test_large_csv(self):
        rows = ["date,amount"] + [f"2024-01-{i:02d},{i * 10}.00" for i in range(1, 101)]
        csv_data = "\n".join(rows).encode("utf-8")
        result = parse_csv(csv_data)
        assert "2024-01-01" in result
        assert "2024-01-100" in result  # last row has day 100

    def test_returns_string(self):
        result = parse_csv(b"hello")
        assert isinstance(result, str)


# ── PDF parsing ──────────────────────────────────────────────────────────────

class TestParsePdf:
    def test_extracts_text(self):
        fake_page = MagicMock()
        fake_page.extract_text.return_value = "Transaction: $50.00 Coffee Shop"

        fake_reader = MagicMock()
        fake_reader.pages = [fake_page]

        with patch("services.parser.PdfReader", return_value=fake_reader):
            result = parse_pdf(b"fake pdf bytes")
            assert "Transaction: $50.00 Coffee Shop" in result

    def test_multiple_pages(self):
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

    def test_empty_page(self):
        page1 = MagicMock()
        page1.extract_text.return_value = None
        page2 = MagicMock()
        page2.extract_text.return_value = "Some content"

        fake_reader = MagicMock()
        fake_reader.pages = [page1, page2]

        with patch("services.parser.PdfReader", return_value=fake_reader):
            result = parse_pdf(b"fake pdf bytes")
            assert "Some content" in result

    def test_all_empty_pages(self):
        page1 = MagicMock()
        page1.extract_text.return_value = None
        page2 = MagicMock()
        page2.extract_text.return_value = None

        fake_reader = MagicMock()
        fake_reader.pages = [page1, page2]

        with patch("services.parser.PdfReader", return_value=fake_reader):
            result = parse_pdf(b"fake pdf bytes")
            assert result == ""

    def test_no_pages(self):
        fake_reader = MagicMock()
        fake_reader.pages = []

        with patch("services.parser.PdfReader", return_value=fake_reader):
            result = parse_pdf(b"fake pdf bytes")
            assert result == ""

    def test_strips_trailing_whitespace(self):
        page = MagicMock()
        page.extract_text.return_value = "  content with spaces  "

        fake_reader = MagicMock()
        fake_reader.pages = [page]

        with patch("services.parser.PdfReader", return_value=fake_reader):
            result = parse_pdf(b"fake pdf bytes")
            assert not result.endswith(" ")
            assert not result.endswith("\n")

    def test_pages_separated_by_newlines(self):
        page1 = MagicMock()
        page1.extract_text.return_value = "Page1"
        page2 = MagicMock()
        page2.extract_text.return_value = "Page2"

        fake_reader = MagicMock()
        fake_reader.pages = [page1, page2]

        with patch("services.parser.PdfReader", return_value=fake_reader):
            result = parse_pdf(b"fake pdf bytes")
            # Pages should be separated (not concatenated directly)
            assert "Page1" in result
            assert "Page2" in result
            assert result != "Page1Page2"

    def test_unicode_in_pdf(self):
        page = MagicMock()
        page.extract_text.return_value = "Total: \u00a5500 \u20ac200"

        fake_reader = MagicMock()
        fake_reader.pages = [page]

        with patch("services.parser.PdfReader", return_value=fake_reader):
            result = parse_pdf(b"fake pdf bytes")
            assert "\u00a5500" in result
            assert "\u20ac200" in result

    def test_passes_bytes_as_bytesio(self):
        """Ensure parse_pdf wraps bytes in BytesIO before passing to PdfReader."""
        fake_reader = MagicMock()
        fake_reader.pages = []

        with patch("services.parser.PdfReader", return_value=fake_reader) as mock_reader:
            parse_pdf(b"test bytes")
            args = mock_reader.call_args[0]
            # Should be called with a BytesIO object
            import io
            assert isinstance(args[0], io.BytesIO)
