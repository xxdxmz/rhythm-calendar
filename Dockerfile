FROM mcr.microsoft.com/playwright/python:v1.61.0-noble

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
RUN mkdir -p /app/data/raw

ENV RHYTHM_DATABASE_PATH=/app/data/rhythm_calendar.sqlite3 \
    BILIBILI_BROWSER_HEADLESS=true \
    ARCAEA_FETCH_INTERVAL_MINUTES=60

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
