"""
Симулирует вебхук от Tribute для тестирования без реальных платежей.
Запускать ПОСЛЕ запуска бота (run.py).

Использование:
    python test_webhook.py <telegram_id> <service>
    python test_webhook.py 800730615 ai
    python test_webhook.py 800730615 expert
"""
import sys
import hmac
import hashlib
import json
import urllib.request

from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).parent / ".env")

TRIBUTE_API_KEY = os.getenv("TRIBUTE_API_KEY", "")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8080"))
PRODUCT_IDS = {"ai": 130557, "expert": 130596}

def send_test_webhook(telegram_id: int, service: str):
    product_id = PRODUCT_IDS.get(service)
    if not product_id:
        print(f"Неизвестный сервис: {service}. Используй 'ai' или 'expert'.")
        sys.exit(1)

    payload = {
        "type": "order.created",
        "payload": {
            "product": {"id": product_id},
            "buyer": {"telegram_id": telegram_id},
            "amount": 700 if service == "ai" else 2500,
            "currency": "eur",
        }
    }

    body = json.dumps(payload).encode()
    signature = hmac.new(TRIBUTE_API_KEY.encode(), body, hashlib.sha256).hexdigest()

    req = urllib.request.Request(
        f"http://localhost:{WEBHOOK_PORT}/tribute/webhook",
        data=body,
        headers={
            "Content-Type": "application/json",
            "trbt-signature": signature,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            print(f"✅ Вебхук отправлен. Статус: {resp.status}")
            print(f"   telegram_id={telegram_id}, сервис={service}, product_id={product_id}")
    except urllib.error.HTTPError as e:
        print(f"❌ Ошибка: {e.code} {e.reason}")
    except urllib.error.URLError as e:
        print(f"❌ Сервер недоступен: {e.reason}")
        print("   Убедись что бот запущен (run.py)")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Использование: python test_webhook.py <telegram_id> <ai|expert>")
        print("Пример:        python test_webhook.py 800730615 ai")
        sys.exit(1)

    send_test_webhook(int(sys.argv[1]), sys.argv[2])
