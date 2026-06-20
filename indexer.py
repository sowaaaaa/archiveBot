"""
Индексация базы знаний: фото + описания из data/knowledge/ + PDF из data/pdfs/
Запускать один раз после добавления новых материалов: python indexer.py

Форматы:
  Одиночный пост:   data/knowledge/name.jpg  +  data/knowledge/name.txt
  Пост с несколькими фото:  data/knowledge/name/1.jpg, 2.jpg...  +  description.txt
"""
import os
import base64
import glob
import fitz  # pymupdf
import chromadb
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
KNOWLEDGE_DIR = "data/knowledge"
PDFS_DIR = "data/pdfs"
DB_DIR = "data/chroma_db"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

client = Anthropic(api_key=ANTHROPIC_API_KEY)
chroma = chromadb.PersistentClient(path=DB_DIR)
collection = chroma.get_or_create_collection(
    name="archive_knowledge",
    metadata={"hnsw:space": "cosine"},
)


# ── Работа с изображениями ────────────────────────────────────────────────────

def encode_image(path: str) -> tuple[str, str]:
    ext = os.path.splitext(path)[1].lower()
    media_map = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".webp": "image/webp", ".gif": "image/gif",
    }
    with open(path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode(), media_map.get(ext, "image/jpeg")


def claude_describe(image_paths: list[str], hint_text: str = "") -> str:
    """Отправляет одно или несколько изображений в Claude, получает описание."""
    content = []

    for path in image_paths:
        b64, media_type = encode_image(path)
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": media_type, "data": b64},
        })

    hint = f"\n\nТекст из поста:\n{hint_text.strip()}" if hint_text.strip() else ""
    count = len(image_paths)
    img_word = "изображени" + ("е" if count == 1 else "я" if count < 5 else "й")

    content.append({
        "type": "text",
        "text": (
            f"Ты эксперт по физической антропологии. "
            f"Изучи {'это' if count == 1 else f'эти {count}'} {img_word} "
            f"и создай подробное текстовое описание для научной базы знаний.\n\n"
            "Включи всё что видишь:\n"
            "- что именно показано (тип признака, классификация)\n"
            "- названия всех типов и форм с характеристиками\n"
            "- числовые индексы и пропорции если есть\n"
            "- диагностические критерии для определения типа\n"
            "- связи между изображениями если их несколько\n\n"
            "Пиши подробно на русском языке."
            + hint
        ),
    })

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        messages=[{"role": "user", "content": content}],
    )
    return response.content[0].text


def is_image(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in IMAGE_EXTENSIONS


def read_hint(path: str) -> str:
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    return ""


# ── Индексация папки knowledge/ ──────────────────────────────────────────────

def index_knowledge():
    if not os.path.exists(KNOWLEDGE_DIR):
        print(f"  Папка {KNOWLEDGE_DIR}/ не найдена")
        return

    entries = sorted(os.listdir(KNOWLEDGE_DIR))
    posts = []  # каждый пост: (doc_id, [image_paths], hint_text, label)

    for entry in entries:
        full = os.path.join(KNOWLEDGE_DIR, entry)
        stem, ext = os.path.splitext(entry)

        # Пропускаем .txt и пример
        if ext.lower() == ".txt" or entry.startswith("ПРИМЕР"):
            continue

        if os.path.isdir(full):
            # Папка = пост с несколькими фото
            images = sorted([
                os.path.join(full, f)
                for f in os.listdir(full)
                if is_image(os.path.join(full, f))
            ])
            if not images:
                continue
            hint = read_hint(os.path.join(full, "description.txt"))
            posts.append((f"post_{entry}", images, hint, entry))

        elif is_image(full):
            # Одиночная картинка
            hint = read_hint(os.path.join(KNOWLEDGE_DIR, stem + ".txt"))
            posts.append((f"img_{stem}", [full], hint, entry))

    if not posts:
        print(f"  Нет материалов в {KNOWLEDGE_DIR}/")
        return

    print(f"\n📸 Найдено {len(posts)} постов в {KNOWLEDGE_DIR}/")

    for doc_id, images, hint, label in posts:
        existing = collection.get(ids=[doc_id])
        if existing["ids"]:
            print(f"  ⏭  {label} — уже в базе")
            continue

        n = len(images)
        print(f"  🔍 {label} ({n} фото) — отправляю в Claude...")
        try:
            description = claude_describe(images, hint)
            collection.add(
                documents=[description],
                ids=[doc_id],
                metadatas=[{
                    "source": label,
                    "type": "image",
                    "images_count": n,
                }],
            )
            print(f"  ✅ Добавлено ({len(description)} символов)")
        except Exception as e:
            print(f"  ❌ Ошибка {label}: {e}")


# ── Индексация PDF-книг ───────────────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = 600, overlap: int = 80) -> list[str]:
    words = text.split()
    chunks, i = [], 0
    while i < len(words):
        chunks.append(" ".join(words[i: i + chunk_size]))
        i += chunk_size - overlap
    return chunks


def index_pdfs():
    pdf_files = glob.glob(os.path.join(PDFS_DIR, "*.pdf"))
    if not pdf_files:
        print(f"  Нет PDF в {PDFS_DIR}/")
        return

    print(f"\n📚 Найдено {len(pdf_files)} PDF в {PDFS_DIR}/")

    for pdf_path in pdf_files:
        book_name = os.path.splitext(os.path.basename(pdf_path))[0]
        print(f"  📖 {book_name}...")
        try:
            doc = fitz.open(pdf_path)
            full_text = "\n".join(
                page.get_text() for page in doc if page.get_text().strip()
            )
            chunks = chunk_text(full_text)
            added = 0
            for i, chunk in enumerate(chunks):
                doc_id = f"pdf_{book_name}_{i}"
                if not collection.get(ids=[doc_id])["ids"]:
                    collection.add(
                        documents=[chunk],
                        ids=[doc_id],
                        metadatas=[{"source": book_name, "type": "pdf", "chunk": i}],
                    )
                    added += 1
            print(f"  ✅ {added} новых чанков (всего {len(chunks)})")
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")


# ── Статистика ────────────────────────────────────────────────────────────────

def print_stats():
    total = collection.count()
    print(f"\n📊 База знаний: {total} записей")
    if total > 0:
        sources: dict[str, int] = {}
        for m in collection.get(include=["metadatas"])["metadatas"]:
            src = m.get("source", "?")
            sources[src] = sources.get(src, 0) + 1
        for src, count in sorted(sources.items()):
            print(f"   {src}: {count} записей")


# ── Запуск ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not ANTHROPIC_API_KEY:
        print("❌ ANTHROPIC_API_KEY не задан в .env")
        exit(1)

    print("🏰 Индексация базы знаний «Архива Происхождения»")
    print("=" * 50)

    index_knowledge()
    index_pdfs()
    print_stats()

    print("\n✅ Готово. Теперь запусти python run.py")
