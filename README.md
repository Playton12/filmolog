# 🎬 Filmolog — Твой личный киноколлекционер

Telegram-бот для управления коллекцией фильмов, сериалов и аниме.  
Добавляй, редактируй, отмечай просмотренные — всё в одном месте.


## ✨ Возможности

- 📥 Добавление контента с названием, жанром, описанием и постером
- 🖼 Поддержка постеров (фото в Telegram)
- 🎯 Рекомендации по жанрам
- 📅 Отслеживание дат добавления и просмотра
- 📊 Статистика и прогресс
- 🔍 Поиск и редактирование
- 🗑 Умное удаление с подтверждением
- 🌐 Деплой на [Fly.io](https://fly.io) с persistent volume для БД

## 🛠 Технологии
- Python 3.12
- aiogram 3 — Telegram-фреймворк
- aiosqlite — асинхронная SQLite
- thefuzz — нечёткий поиск названий
- Fly.io — хостинг с persistent volume

## 🚀 Деплой на Fly.io

```bash
# 1. Установить flyctl
curl -L https://fly.io/install.sh | sh

# 2. Авторизоваться
fly auth login

# 3. Создать приложение
fly launch

# 4. Создать persistent volume для БД
fly volumes create data --region ams --size 1

# 5. Задать токен бота
fly secrets set BOT_TOKEN=your_token_here

# 6. Задеплоить
fly deploy
```

## Создан с ❤️ для киноманов
