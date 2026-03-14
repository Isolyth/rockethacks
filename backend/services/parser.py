import io

from pypdf import PdfReader

from config import MAX_PDF_PAGES


def parse_pdf(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    if len(reader.pages) > MAX_PDF_PAGES:
        raise ValueError(f"PDF exceeds maximum of {MAX_PDF_PAGES} pages")
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
        text += "\n"
    return text.strip()


def parse_csv(content: bytes) -> str:
    return content.decode("utf-8", errors="replace")
