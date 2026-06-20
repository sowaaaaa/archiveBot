# Архив Происхождения

Telegram-бот для антропологического анализа внешности на основе фотографий.

## Структура

```
archive-bot/
├── bot/
│   ├── handlers/
│   │   ├── start.py          # Приветствие, выбор языка
│   │   ├── payment.py        # Обработка оплаты через Tribute
│   │   ├── collection.py     # Сбор фотографий и данных
│   │   ├── analysis.py       # Запуск анализа, анимация загрузки
│   │   └── admin.py          # Панель администратора
│   ├── services/
│   │   ├── ai_service.py     # Анализ через Claude + RAG
│   │   ├── face_metrics.py   # Антропометрия через MediaPipe
│   │   └── pdf_service.py    # Генерация PDF-хроники
│   ├── keyboards/
│   │   └── inline.py         # Инлайн-клавиатуры
│   ├── database/
│   │   └── db.py             # SQLite: пользователи, платежи, заявки
│   ├── i18n.py               # Тексты RU / EN
│   ├── states.py             # FSM-состояния
│   └── config.py             # Конфигурация из .env
├── assets/                   # Фото интерфейса, шрифты (Git LFS)
├── data/
│   ├── knowledge/            # ChromaDB — база антропологических знаний
│   └── pdfs/                 # Источники для RAG (Git LFS)
├── webhook_server.py         # Вебхук Tribute
├── run.py                    # Точка входа
└── requirements.txt
```

## Стек

- **aiogram 3.29** — Telegram Bot API 9.4
- **Anthropic Claude** — анализ и генерация текста
- **MediaPipe** — антропометрические метрики лица
- **ChromaDB** — векторная база знаний (RAG)
- **Pillow + PyMuPDF** — генерация PDF-хроники
- **aiohttp** — вебхук-сервер для Tribute
- **SQLite** — хранение пользователей и платежей
