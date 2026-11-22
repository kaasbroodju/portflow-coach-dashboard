"""The text of a file, for the AI advice (spec 040, F7).

Word, PowerPoint and Excel: from the original (a zip with XML, no extra package; Excel via
xlsx_reader, like the Excel import of spec 013). Pdf: with pypdf, if installed. Returns None when the
text cannot be read; the caller then sends only the name.
"""

import io
import re
import zipfile
from xml.etree import ElementTree

from . import xlsx_reader

DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
PPTX = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
MAX_BYTES = 50 * 1024 * 1024
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


def readable(mime: str) -> bool:
    return mime in (DOCX, PPTX, XLSX, "application/pdf")


def _tidy(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _docx(archive: zipfile.ZipFile) -> str:
    root = ElementTree.fromstring(archive.read("word/document.xml"))
    paragraphs = []
    for p in root.iter(f"{W}p"):
        paragraphs.append("".join(t.text or "" for t in p.iter(f"{W}t")))
    return "\n".join(paragraphs)


def _pptx(archive: zipfile.ZipFile) -> str:
    def number(name: str) -> int:
        match = re.search(r"(\d+)\.xml$", name)
        return int(match.group(1)) if match else 0
    slides = sorted((n for n in archive.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)), key=number)
    out = []
    for name in slides:
        root = ElementTree.fromstring(archive.read(name))
        lines = ["".join(t.text or "" for t in p.iter(f"{A}t")) for p in root.iter(f"{A}p")]
        out.append(f"Dia {number(name)}:\n" + "\n".join(line for line in lines if line.strip()))
    return "\n\n".join(out)


def _xlsx(data: bytes) -> str:
    out = []
    for sheet in xlsx_reader.read_workbook(data):
        rows = ["\t".join(cell for cell in row) for row in sheet.rows if any(c.strip() for c in row)]
        out.append(f"Blad {sheet.name}:\n" + "\n".join(rows))
    return "\n\n".join(out)


def _pdf(data: bytes) -> str | None:
    try:
        from pypdf import PdfReader
    except ImportError:   # spec 040, technical requirement: without pypdf only the name goes
        return None
    reader = PdfReader(io.BytesIO(data))
    return "\n\n".join((page.extract_text() or "") for page in reader.pages)


def text_of(data: bytes, mime: str) -> str | None:
    """The text of a file, or None if it cannot be read."""
    if not data or len(data) > MAX_BYTES:
        return None
    try:
        if mime == "application/pdf":
            text = _pdf(data)
        elif mime == XLSX:
            text = _xlsx(data)
        elif mime in (DOCX, PPTX):
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                text = _docx(archive) if mime == DOCX else _pptx(archive)
        else:
            return None
    except Exception:   # a damaged or unusual file: only the name goes (F7)
        return None
    return _tidy(text) if text and text.strip() else None
