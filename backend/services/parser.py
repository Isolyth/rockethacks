import io
from pypdf import PdfReader


def parse_pdf(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
        text += "\n"
    return text.strip()


def parse_csv(content: bytes) -> str:
    return content.decode("utf-8")
