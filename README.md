# Intermediary Matching Bot

Telegram-бот для посредничества между микроблогерами (1K–10K) и селлерами маркетплейсов (Wildberries / OZON).

## Функции
- 🛒 **Селлер** — создаёт заявку на товар, бот подбирает блогеров по нише
- 📱 **Блогер** — регистрируется в базе, ждёт уведомлений о товарах
- ⚙️ **Админ** — статистика, списки, экспорт данных

## Установка

```bash
git clone https://github.com/annakazinets16-a11y/intermediary-matching-bot.git
cd intermediary-matching-bot
pip install -r requirements.txt
```

## Настройка

Создай `.env`:
```
MATCHING_BOT_TOKEN=your_bot_token_from_BotFather
ADMIN_ID=your_telegram_id
```

## Запуск

```bash
python bot.py
```

## Деплой

Render / Railway / VPS — любой хостинг с Python 3.11+.

## Бизнес-модель
- Подписка селлера: 990 ₽/мес за 10 подборов
- Или комиссия: 200 ₽ за каждый успешный мэтч
- Фримиум: 2 бесплатных подбора для теста

## Контакты
- Telegram: @annakazinets
- GitHub: github.com/annakazinets16-a11y
