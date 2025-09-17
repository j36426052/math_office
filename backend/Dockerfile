# Backend Dockerfile
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ADMIN_USER=qsnake \
    ADMIN_PASS=jst101101101
WORKDIR /app
# System deps (if any needed later)
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app /app/app
EXPOSE 8000
# Default to production run
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
