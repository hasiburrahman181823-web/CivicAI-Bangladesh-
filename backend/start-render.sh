#!/bin/sh
set -eu

export ALLOWED_HOSTS="${ALLOWED_HOSTS:-${RENDER_EXTERNAL_HOSTNAME:-}}"

if [ -z "${CIVICAI_ARTIFACTS:-}" ] && [ ! -f /app/backend/ml_training/artifacts/sha256.json ]; then
    export CIVICAI_ARTIFACTS=/app/release-models
    export CIVICAI_MODEL_MANIFEST_SHA256="${CIVICAI_MODEL_MANIFEST_SHA256:-f6a7f813aa57f273ed8752602d6cd883b3c434412e442f9350a5af93b2cc5dab}"
fi

exec uvicorn backend.app.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8000}" \
    --workers 1 \
    --no-server-header \
    --no-proxy-headers \
    --limit-concurrency 32 \
    --timeout-keep-alive 5 \
    --no-access-log
