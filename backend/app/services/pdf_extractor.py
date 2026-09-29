"""Text extraction for purchase order PDFs."""

import logging
from pathlib import Path

import pdfplumber
from pdfminer.pdfdocument import PDFPasswordIncorrect
from pdfplumber.utils.exceptions import MalformedPDFException, PdfminerException

from app.exceptions import PDFExtractionError

logger = logging.getLogger(__name__)

_PDF_ERRORS = (OSError, MalformedPDFException)


def extract_text_from_pdf(path: Path | str) -> str:
    """Extract the concatenated text of every page, or raise PDFExtractionError."""
    name = Path(path).name
    try:
        with pdfplumber.open(path) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
    except PdfminerException as exc:
        if _is_password_error(exc):
            raise PDFExtractionError(
                "PDF is password-protected. Please remove the password and re-upload."
            ) from exc
        detail = str(exc) or type(exc).__name__
        raise PDFExtractionError(f"could not read PDF '{name}': {detail}") from exc
    except _PDF_ERRORS as exc:
        raise PDFExtractionError(f"could not read PDF '{name}': {exc}") from exc

    text = "\n".join(pages).strip()
    if not text:
        raise PDFExtractionError(
            f"no extractable text in '{name}'; the document is likely a scanned image"
        )
    logger.info("extracted %d characters from %s", len(text), name)
    return text


def _is_password_error(exc: BaseException) -> bool:
    """Walk the wrapped-exception chain looking for pdfminer's password errors."""
    seen: set[int] = set()
    node: BaseException | None = exc
    while node is not None and id(node) not in seen:
        seen.add(id(node))
        if isinstance(node, PDFPasswordIncorrect):
            return True
        node = node.__cause__ or node.__context__
    return False
