from html.parser import HTMLParser
from importlib.util import find_spec
from pathlib import Path


class MissingExtractorDependency(RuntimeError):
    pass


class UnsupportedFileType(RuntimeError):
    pass


TEXT_EXTENSIONS = {".md", ".markdown", ".txt", ".rst", ".log"}
HTML_EXTENSIONS = {".html", ".htm"}
PDF_EXTENSIONS = {".pdf"}
DOCX_EXTENSIONS = {".docx"}
RTF_EXTENSIONS = {".rtf"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"}

OPTIONAL_EXTENSIONS = PDF_EXTENSIONS | DOCX_EXTENSIONS | RTF_EXTENSIONS | IMAGE_EXTENSIONS
KNOWN_EXTENSIONS = TEXT_EXTENSIONS | HTML_EXTENSIONS | OPTIONAL_EXTENSIONS


class ExtractedText:
    def __init__(self, text: str, extractor: str) -> None:
        self.text = text
        self.extractor = extractor


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        stripped_data = data.strip()
        if stripped_data:
            self.parts.append(stripped_data)

    def text(self) -> str:
        return "\n".join(self.parts)


def can_extract_extension(extension: str, enable_ocr: bool = False) -> bool:
    normalized_extension = extension.lower()
    if normalized_extension in TEXT_EXTENSIONS | HTML_EXTENSIONS:
        return True
    if normalized_extension in PDF_EXTENSIONS:
        return _module_available("pypdf")
    if normalized_extension in DOCX_EXTENSIONS:
        return _module_available("docx")
    if normalized_extension in RTF_EXTENSIONS:
        return _module_available("striprtf")
    if normalized_extension in IMAGE_EXTENSIONS:
        return enable_ocr and _module_available("PIL") and _module_available("pytesseract")
    return False


def extract_text(path: Path, enable_ocr: bool = False) -> ExtractedText:
    extension = path.suffix.lower()
    if extension in TEXT_EXTENSIONS:
        return ExtractedText(path.read_text(encoding="utf-8", errors="ignore"), "text")
    if extension in HTML_EXTENSIONS:
        return ExtractedText(_extract_html(path), "html")
    if extension in PDF_EXTENSIONS:
        return ExtractedText(_extract_pdf(path), "pypdf")
    if extension in DOCX_EXTENSIONS:
        return ExtractedText(_extract_docx(path), "python-docx")
    if extension in RTF_EXTENSIONS:
        return ExtractedText(_extract_rtf(path), "striprtf")
    if extension in IMAGE_EXTENSIONS:
        if not enable_ocr:
            raise MissingExtractorDependency("OCR is disabled for image extraction.")
        return ExtractedText(_extract_image_ocr(path), "pytesseract")
    raise UnsupportedFileType(f"Unsupported file type: {extension}")


def _extract_html(path: Path) -> str:
    parser = _HTMLTextExtractor()
    parser.feed(path.read_text(encoding="utf-8", errors="ignore"))
    return parser.text()


def _extract_pdf(path: Path) -> str:
    if not _module_available("pypdf"):
        raise MissingExtractorDependency("Install the backend ingest extra to read PDF files.")
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages: list[str] = []
    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        if page_text.strip():
            pages.append(f"Page {page_number}\n{page_text.strip()}")
    return "\n\n".join(pages)


def _extract_docx(path: Path) -> str:
    if not _module_available("docx"):
        raise MissingExtractorDependency("Install the backend ingest extra to read DOCX files.")
    from docx import Document

    document = Document(str(path))
    return "\n".join(paragraph.text for paragraph in document.paragraphs if paragraph.text.strip())


def _extract_rtf(path: Path) -> str:
    if not _module_available("striprtf"):
        raise MissingExtractorDependency("Install the backend ingest extra to read RTF files.")
    from striprtf.striprtf import rtf_to_text

    return rtf_to_text(path.read_text(encoding="utf-8", errors="ignore"))


def _extract_image_ocr(path: Path) -> str:
    if not (_module_available("PIL") and _module_available("pytesseract")):
        raise MissingExtractorDependency("Install the backend ingest extra and Tesseract to OCR images.")
    from PIL import Image
    import pytesseract

    with Image.open(path) as image:
        return pytesseract.image_to_string(image)


def _module_available(module_name: str) -> bool:
    return find_spec(module_name) is not None