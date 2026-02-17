# backend/Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application (Railway provides PORT env var)
<<<<<<< HEAD
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
=======
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
