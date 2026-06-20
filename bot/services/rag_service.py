import os
import glob
import pdfplumber
from pathlib import Path

_rag_context: str = ""


def load_pdfs(pdf_dir: str = "data/pdfs") -> str:
    global _rag_context
    texts = []
    pdf_files = glob.glob(os.path.join(pdf_dir, "*.pdf"))

    for pdf_path in pdf_files:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                file_text = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        file_text.append(text.strip())
                if file_text:
                    name = Path(pdf_path).stem
                    texts.append(f"[Источник: {name}]\n" + "\n".join(file_text))
        except Exception as e:
            print(f"Ошибка загрузки PDF {pdf_path}: {e}")

    _rag_context = "\n\n---\n\n".join(texts)
    if _rag_context:
        print(f"RAG: загружено {len(pdf_files)} PDF, {len(_rag_context)} символов")
    else:
        print("RAG: PDF-источники не найдены, анализ будет без RAG-контекста")

    return _rag_context


def get_rag_context() -> str:
    return _rag_context
