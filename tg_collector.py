"""
Автоматический сбор постов из Telegram-канала/чата.
Сохраняет фото + описания в data/knowledge/ в формате для indexer.py

Запуск: python tg_collector.py
"""
import os
import asyncio
import re
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument

load_dotenv()

API_ID = int(os.getenv("TG_API_ID", "0"))
API_HASH = os.getenv("TG_API_HASH", "")
KNOWLEDGE_DIR = "data/knowledge"

IMAGE_MIME = {"image/jpeg", "image/png", "image/webp"}


def safe_name(text: str, max_len: int = 40) -> str:
    """Превращает текст в безопасное имя папки/файла."""
    name = re.sub(r'[\\/*?:"<>|]', "", text)
    name = name.strip().replace(" ", "_")[:max_len]
    return name or "post"


async def collect(channel_link: str, limit: int = 0):
    async with TelegramClient("tg_session", API_ID, API_HASH) as client:
        print(f"\n📡 Подключаюсь к {channel_link}...")
        entity = await client.get_entity(channel_link)
        print(f"✅ Канал: {entity.title if hasattr(entity, 'title') else channel_link}")

        os.makedirs(KNOWLEDGE_DIR, exist_ok=True)

        # Собираем все сообщения
        messages = []
        async for msg in client.iter_messages(entity, limit=limit or None):
            messages.append(msg)
        messages.reverse()  # от старых к новым

        print(f"📬 Всего сообщений: {len(messages)}")

        # Группируем альбомы (посты с несколькими фото)
        # Telegram помечает альбомы одинаковым grouped_id
        groups: dict = {}   # grouped_id → [messages]
        singles = []        # одиночные сообщения

        for msg in messages:
            if not msg.media:
                continue
            if msg.grouped_id:
                groups.setdefault(msg.grouped_id, []).append(msg)
            else:
                singles.append(msg)

        total_posts = len(singles) + len(groups)
        print(f"📸 Постов с фото: {total_posts} "
              f"({len(singles)} одиночных, {len(groups)} альбомов)\n")

        saved = 0

        # ── Одиночные сообщения ─────────────────────────────────────────────
        for msg in singles:
            if not _has_photo(msg):
                continue

            # Имя файла: дата + первые слова подписи
            caption = (msg.text or "").strip()
            date_str = msg.date.strftime("%Y%m%d_%H%M%S")
            name = safe_name(caption[:30]) if caption else date_str
            name = f"{date_str}_{name}" if caption else date_str

            img_path = os.path.join(KNOWLEDGE_DIR, name + ".jpg")
            txt_path = os.path.join(KNOWLEDGE_DIR, name + ".txt")

            if os.path.exists(img_path):
                print(f"  ⏭  {name} — уже существует")
                continue

            print(f"  ⬇  {name}...", end=" ", flush=True)
            await client.download_media(msg, img_path)

            if caption:
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(caption)

            saved += 1
            print("✅")

        # ── Альбомы (несколько фото) ────────────────────────────────────────
        for group_id, group_msgs in groups.items():
            # Подпись берём из первого сообщения с текстом
            caption = ""
            for m in group_msgs:
                if m.text and m.text.strip():
                    caption = m.text.strip()
                    break

            date_str = group_msgs[0].date.strftime("%Y%m%d_%H%M%S")
            name = safe_name(caption[:30]) if caption else f"album_{date_str}"
            folder = os.path.join(KNOWLEDGE_DIR, f"{date_str}_{name}")

            if os.path.exists(folder):
                print(f"  ⏭  {name} — уже существует")
                continue

            os.makedirs(folder, exist_ok=True)
            print(f"  ⬇  {name} ({len(group_msgs)} фото)...", end=" ", flush=True)

            photo_num = 1
            for m in sorted(group_msgs, key=lambda x: x.id):
                if not _has_photo(m):
                    continue
                img_path = os.path.join(folder, f"{photo_num}.jpg")
                await client.download_media(m, img_path)
                photo_num += 1

            if caption:
                txt_path = os.path.join(folder, "description.txt")
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(caption)

            saved += 1
            print("✅")

        print(f"\n✅ Сохранено {saved} постов в {KNOWLEDGE_DIR}/")
        print("Теперь запусти: python indexer.py")


def _has_photo(msg) -> bool:
    if isinstance(msg.media, MessageMediaPhoto):
        return True
    if isinstance(msg.media, MessageMediaDocument):
        mime = getattr(msg.media.document, "mime_type", "")
        return mime in IMAGE_MIME
    return False


if __name__ == "__main__":
    if not API_ID or not API_HASH:
        print("❌ Добавь в .env:")
        print("   TG_API_ID=12345678")
        print("   TG_API_HASH=abcdef1234567890abcdef1234567890")
        print("\nПолучить на: https://my.telegram.org/apps")
        exit(1)

    print("🏰 Сборщик постов для «Архива Происхождения»")
    print("=" * 50)
    print("Вставь ссылку на канал или @username:")
    channel = input(">>> ").strip()

    print("Сколько последних сообщений скачать? (Enter = все):")
    limit_str = input(">>> ").strip()
    limit = int(limit_str) if limit_str.isdigit() else 0

    asyncio.run(collect(channel, limit))
