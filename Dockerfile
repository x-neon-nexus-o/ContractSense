FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    DATA_DIR=/data

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --system --no-create-home --home-dir /app --shell /usr/sbin/nologin contractsense \
    && mkdir -p /data \
    && chown -R contractsense:contractsense /app /data

COPY --chown=contractsense:contractsense backend ./backend
COPY --chown=contractsense:contractsense frontend/web ./frontend/web

RUN pip install --no-cache-dir -r backend/requirements.txt

USER contractsense
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=3)" || exit 1

CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
