FROM node:22-slim AS frontend
WORKDIR /web
COPY package*.json ./
RUN npm ci
COPY index.html vite.config.js ./
COPY frontend ./frontend
COPY public ./public
RUN npm run build

FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
RUN groupadd -g 10001 civicai && useradd -r -u 10001 -g civicai civicai \
    && install -d -o 10001 -g 10001 -m 0700 /data
COPY backend/requirements.txt backend/requirements-ml.txt /app/backend/
RUN pip install --no-cache-dir -r backend/requirements.txt -r backend/requirements-ml.txt
COPY backend /app/backend
COPY --from=frontend /web/dist /app/dist
USER 10001:10001
EXPOSE 8000
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-server-header", "--no-proxy-headers", "--limit-concurrency", "32", "--timeout-keep-alive", "5", "--no-access-log"]
