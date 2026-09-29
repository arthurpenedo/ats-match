"""Extração de texto de currículos e vagas em PDF, DOCX, Markdown ou texto puro.

Um ATS só enxerga o que consegue extrair. Se o PDF é uma imagem (escaneado ou exportado
como figura), o texto sai vazio: o currículo fica literalmente invisível para a triagem.
"""

from io import BytesIO
from pathlib import Path

MIN_CHARS_PER_PAGE = 200  # abaixo disso, o PDF provavelmente é imagem


class ExtractionError(ValueError):
    """O arquivo não pôde ser lido ou não tem texto extraível."""


def extract_text(data: bytes, filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        return _pdf(data)
    if suffix == ".docx":
        return _docx(data)
    if suffix in {".md", ".txt", ""}:
        return data.decode("utf-8", errors="replace")
    raise ExtractionError(f"Formato não suportado: {suffix}. Use PDF, DOCX, MD ou TXT.")


def read_file(path: str | Path) -> str:
    path = Path(path)
    return extract_text(path.read_bytes(), path.name)


def _pdf(data: bytes) -> str:
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError

    try:
        reader = PdfReader(BytesIO(data))
        pages = [page.extract_text() or "" for page in reader.pages]
    except PdfReadError as exc:
        raise ExtractionError(f"PDF inválido ou corrompido: {exc}") from exc
    text = "\n".join(pages).strip()
    if len(text) < MIN_CHARS_PER_PAGE * max(len(pages), 1) / 2:
        raise ExtractionError(
            "Quase nenhum texto foi extraído deste PDF. Ele parece ser uma imagem (escaneado ou "
            "exportado como figura), e um ATS também não conseguiria lê-lo. Exporte o currículo como "
            "PDF de texto (ex.: Word ou Google Docs → Salvar como PDF)."
        )
    return text


def _docx(data: bytes) -> str:
    from docx import Document

    try:
        doc = Document(BytesIO(data))
    except Exception as exc:  # python-docx lança vários tipos para arquivos inválidos
        raise ExtractionError(f"DOCX inválido: {exc}") from exc
    parts = [p.text for p in doc.paragraphs]
    for table in doc.tables:  # muitos modelos de currículo usam tabelas para layout
        for row in table.rows:
            parts.extend(cell.text for cell in row.cells)
    return "\n".join(p for p in parts if p.strip())
