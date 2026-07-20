import re
import sys

from pypdf import PdfReader
from pypdf.errors import PdfReadError

MAX_RESUME_CHARS = 24_000
MIN_RESUME_CHARS = 200
MIN_JD_CHARS = 100
MAX_RESUME_PAGES = 2


def read_resume_pdf(path: str) -> str:
    """Read a résumé PDF file and return its cleaned text content.

    Raises:
        ValueError: if the file cannot be found/opened, or if the extracted
            text is too short (suggesting the PDF is image-based/scanned).
    """
    try:
        reader = PdfReader(path)
    except FileNotFoundError:
        raise ValueError(f"Resume PDF not found: {path}")
    except PdfReadError as exc:
        raise ValueError(f"Could not open resume PDF '{path}': {exc}")
    except Exception as exc:
        raise ValueError(f"Could not open resume PDF '{path}': {exc}")

    num_pages = len(reader.pages)
    if num_pages > MAX_RESUME_PAGES:
        print(
            f"Warning: resume '{path}' has {num_pages} pages "
            f"(expected at most {MAX_RESUME_PAGES}).",
            file=sys.stderr,
        )

    pages_text = []
    for page in reader.pages:
        try:
            pages_text.append(page.extract_text() or "")
        except Exception as exc:
            raise ValueError(f"Failed to extract text from resume PDF '{path}': {exc}")

    text = "\n\n".join(pages_text)

    # Collapse runs of 3 or more blank lines down to 2.
    text = re.sub(r"\n{3,}", "\n\n", text)

    if len(text) < MIN_RESUME_CHARS:
        raise ValueError(
            f"Extracted text from '{path}' is too short ({len(text)} characters); "
            "the PDF may be image-based/scanned and requires OCR."
        )

    if len(text) > MAX_RESUME_CHARS:
        print(
            f"Warning: resume text from '{path}' is {len(text)} characters; "
            f"truncating to {MAX_RESUME_CHARS} characters.",
            file=sys.stderr,
        )
        text = text[:MAX_RESUME_CHARS]

    return text


def read_jd_text(path: str) -> str:
    """Read a UTF-8 plain text job description file and return its content.

    Raises:
        ValueError: if the file cannot be found, or if the stripped content
            is shorter than the minimum required length.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        raise ValueError(f"Job description file not found: {path}")
    except OSError as exc:
        raise ValueError(f"Could not open job description file '{path}': {exc}")

    if len(content.strip()) < MIN_JD_CHARS:
        raise ValueError(
            f"Job description file '{path}' has fewer than {MIN_JD_CHARS} "
            "characters of content after stripping whitespace."
        )

    return content
