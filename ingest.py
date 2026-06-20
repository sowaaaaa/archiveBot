"""
Загрузчик статей в ChromaDB для RAG-поиска.

ИСТОЧНИКИ:
  Telegram-посты:  сохрани текст в data/articles/*.txt  (один файл = один источник)
  Telegraph:       добавь URL в data/telegraph_urls.txt  (по одному на строку)

ИСПОЛЬЗОВАНИЕ:
  python ingest.py            # загружает всё
  python ingest.py --clear    # очищает коллекцию и загружает заново

РЕЗУЛЬТАТ:
  Все тексты разбиваются на чанки и сохраняются в ChromaDB (data/chroma_db).
  Бот автоматически использует их при анализе.
"""

import sys
import os
import re
import json
import urllib.request
import urllib.parse
from pathlib import Path

import chromadb

# ── Настройки ─────────────────────────────────────────────────────────────────

KNOWLEDGE_DIR = Path("data/knowledge")
TELEGRAPH_URLS_FILE = Path("data/telegraph_urls.txt")
CHROMA_PATH = "data/chroma_db"
COLLECTION_NAME = "archive_knowledge"
CHUNK_SIZE = 800        # символов в одном чанке
CHUNK_OVERLAP = 100     # перекрытие между чанками


# ── Парсинг Telegraph ─────────────────────────────────────────────────────────

def _fetch_telegraph(url: str) -> tuple[str, str]:
    """Возвращает (заголовок, текст) статьи с telegra.ph через официальное API."""
    # Достаём path из URL: https://telegra.ph/Some-Title-01-01 → Some-Title-01-01
    path = url.rstrip("/").split("telegra.ph/")[-1].split("?")[0]
    api_url = f"https://api.telegra.ph/getPage/{path}?return_content=true"

    req = urllib.request.Request(api_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())

    if not data.get("ok"):
        raise ValueError(f"Telegraph API вернул ошибку для {url}")

    page = data["result"]
    title = page.get("title", path)
    content_nodes = page.get("content", [])

    # Рекурсивно извлекаем текст из nodes
    def extract_text(node) -> str:
        if isinstance(node, str):
            return node
        if not isinstance(node, dict):
            return ""

        tag = node.get("tag", "")
        children = node.get("children", [])

        # Подпись к картинке → [Изображение: текст подписи]
        if tag == "figure":
            caption_node = next((c for c in children if isinstance(c, dict) and c.get("tag") == "figcaption"), None)
            if caption_node:
                caption = "".join(extract_text(c) for c in caption_node.get("children", [])).strip()
                if caption:
                    return f"[Изображение: {caption}]\n"
            return ""  # картинка без подписи — пропускаем

        text = "".join(extract_text(c) for c in children)

        if tag in ("p", "h3", "h4", "blockquote", "li"):
            return text + "\n"
        if tag in ("h3", "h4"):
            return f"\n{text}\n"
        return text

    text = "".join(extract_text(n) for n in content_nodes).strip()
    return title, text


# ── Разбивка на чанки ─────────────────────────────────────────────────────────

def _chunk(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    # Сначала разбиваем по абзацам, затем склеиваем до нужного размера
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    chunks = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 <= size:
            current = (current + "\n\n" + para).strip()
        else:
            if current:
                chunks.append(current)
            # Если абзац сам по себе больше size — режем жёстко
            if len(para) > size:
                for i in range(0, len(para), size - overlap):
                    chunks.append(para[i:i + size])
                current = ""
            else:
                current = para

    if current:
        chunks.append(current)

    return chunks


# ── Загрузка в ChromaDB ───────────────────────────────────────────────────────

def _get_or_create_collection(clear: bool = False) -> chromadb.Collection:
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    if clear:
        try:
            client.delete_collection(COLLECTION_NAME)
            print("Коллекция очищена.")
        except Exception:
            pass
    return client.get_or_create_collection(COLLECTION_NAME)


def _ingest_chunks(collection: chromadb.Collection, chunks: list[str], source: str):
    existing_ids = set()
    try:
        all_ids = collection.get(where={"source": source})["ids"]
        existing_ids = set(all_ids)
    except Exception:
        pass

    ids, docs, metas = [], [], []
    for i, chunk in enumerate(chunks):
        chunk_id = f"{source}_{i}"
        if chunk_id in existing_ids:
            continue
        ids.append(chunk_id)
        docs.append(chunk)
        metas.append({"source": source})

    if ids:
        collection.add(documents=docs, metadatas=metas, ids=ids)

    return len(ids)


# ── Основная логика ───────────────────────────────────────────────────────────

def main():
    clear = "--clear" in sys.argv
    os.makedirs(KNOWLEDGE_DIR, exist_ok=True)

    collection = _get_or_create_collection(clear=clear)
    total_added = 0

    # 1. Файлы из data/knowledge — рекурсивно на любую глубину
    # Плоские *.txt в корне + description.txt в любой вложенной папке
    knowledge_sources: list[tuple[str, Path]] = []

    for path in sorted(KNOWLEDGE_DIR.glob("*.txt")):
        knowledge_sources.append((path.stem, path))

    for desc_path in sorted(KNOWLEDGE_DIR.glob("**/description.txt")):
        # Источник = путь относительно knowledge/, без /description.txt
        source_name = str(desc_path.parent.relative_to(KNOWLEDGE_DIR))
        knowledge_sources.append((source_name, desc_path))

    if knowledge_sources:
        print(f"\n── Knowledge база ({len(knowledge_sources)} источников) ──")
        for source, path in knowledge_sources:
            text = path.read_text(encoding="utf-8-sig").strip()
            if not text:
                print(f"  [пропуск] {source} — пустой файл")
                continue
            chunks = _chunk(text)
            added = _ingest_chunks(collection, chunks, source=source)
            print(f"  {source}: {len(chunks)} чанков, добавлено {added} новых")
            total_added += added
    else:
        print(f"\nKnowledge: нет файлов в {KNOWLEDGE_DIR}/")
        print("  Добавь .txt файлы или папки с description.txt")

    # 2. Telegraph-статьи
    if TELEGRAPH_URLS_FILE.exists():
        urls = [u.strip() for u in TELEGRAPH_URLS_FILE.read_text(encoding="utf-8-sig").splitlines()
                if u.strip() and not u.startswith("#")]
        if urls:
            print(f"\n── Telegraph ({len(urls)} статей) ──")
            for url in urls:
                try:
                    title, text = _fetch_telegraph(url)
                    if not text:
                        print(f"  [пустая] {url}")
                        continue
                    source = re.sub(r"[^\w\-]", "_", title)[:60]
                    chunks = _chunk(text)
                    added = _ingest_chunks(collection, chunks, source=source)
                    print(f"  «{title}»: {len(chunks)} чанков, добавлено {added} новых")
                    total_added += added
                except Exception as e:
                    print(f"  [ошибка] {url}: {e}")
        else:
            print(f"\nTelegraph: файл {TELEGRAPH_URLS_FILE} пуст.")
    else:
        print(f"\nTelegraph: создай {TELEGRAPH_URLS_FILE} и добавь URL по одному на строку.")

    # Итог
    print(f"\n✅ Готово. Добавлено чанков: {total_added}. Всего в базе: {collection.count()}")


if __name__ == "__main__":
    main()
