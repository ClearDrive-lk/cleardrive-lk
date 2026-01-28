# Root Dockerfile – build backend when context is repo root (e.g. Railway)
# Use backend/Dockerfile directly when build context is backend/

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application only
COPY backend/ .

# Expose port
EXPOSE 8000

# Run application (Railway provides PORT env var)
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
