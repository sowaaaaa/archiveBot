import os
from pathlib import Path
from dotenv import load_dotenv

# Явный путь к .env: два уровня вверх от bot/config.py → корень проекта
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(_env_path, override=True)

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

_admin_ids_raw = os.getenv("ADMIN_IDS", "")
ADMIN_IDS: list[int] = [int(x.strip()) for x in _admin_ids_raw.split(",") if x.strip().isdigit()]

ADMIN_CHAT_ID: int | None = int(os.getenv("ADMIN_CHAT_ID", 0)) or None
DB_PATH: str = os.getenv("DB_PATH", "data/archive.db")
CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-opus-4-8")
AI_ENABLED: bool = os.getenv("AI_ENABLED", "true").lower() not in ("false", "0", "no")

# Tribute
TRIBUTE_API_KEY: str = os.getenv("TRIBUTE_API_KEY", "")
TRIBUTE_PRODUCT_AI_IDS: set[int] = {130557, 130602}
TRIBUTE_PRODUCT_EXPERT_IDS: set[int] = {130596, 130618}
TRIBUTE_PRODUCT_TEST_ID: int = 131665
TRIBUTE_LINK_AI: str = "https://t.me/tribute/app?startapp=pyfD"
TRIBUTE_LINK_EXPERT: str = "https://t.me/tribute/app?startapp=pxYK"

# Цены в центах EUR (700 = 7 EUR, 2500 = 25 EUR)
AI_PRICE: int = 700
EXPERT_PRICE: int = 2500

WEBHOOK_PORT: int = int(os.getenv("WEBHOOK_PORT", "8080"))
