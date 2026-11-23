#!/bin/sh
set -eu

export ALLOWED_HOSTS="${ALLOWED_HOSTS:-${RENDER_EXTERNAL_HOSTNAME:-}}"

exec uvicorn backend.app.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8000}" \
    --workers 1 \
    --no-server-header \
    --no-proxy-headers \
    --limit-concurrency 32 \
    --timeout-keep-alive 5 \
    --no-access-log
