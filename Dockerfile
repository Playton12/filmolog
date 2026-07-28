FROM python:3.12-slim

WORKDIR /app

# Кэшируем установку зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Устанавливаем пакет
RUN pip install --no-cache-dir -e .

CMD ["python", "-m", "movie_bot.main"]
