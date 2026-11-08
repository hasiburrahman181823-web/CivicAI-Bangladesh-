# CivicAI Bangladesh - Multi-Stage Production Dockerfile

# Stage 1: Build Frontend Assets
FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Production Python Backend Server
FROM python:3.11-slim AS production
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    ENVIRONMENT=production

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY backend/requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application source code
COPY backend/ ./backend/
COPY database/ ./database/
COPY ai/ ./ai/
COPY datasets/ ./datasets/
COPY training/ ./training/
COPY scripts/ ./scripts/
COPY .env.example ./.env

# Copy built frontend static distribution
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Ensure upload directory exists
RUN mkdir -p /app/uploads

EXPOSE 8000

# Health check probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Production startup command
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
