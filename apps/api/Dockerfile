FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1     PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY requirements-prod.txt .
RUN set -eux; for attempt in 1 2 3; do pip install --no-cache-dir --retries 10 --timeout 60 -r requirements-prod.txt && exit 0; echo "dependency install attempt ${attempt} failed; retrying" >&2; sleep 3; done; exit 1

COPY app ./app
COPY alembic.ini .
COPY alembic ./alembic

RUN mkdir -p /data/uploads && chown -R app:app /app /data/uploads
USER app

EXPOSE 8000

ENV UVICORN_WORKERS=2
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS:-2} --proxy-headers --forwarded-allow-ips='*' --no-access-log"]
