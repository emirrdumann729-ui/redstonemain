# Written with SI assistance (Claude, Anthropic) for NASA Space Apps 2026; see SI_DISCLOSURE.md.
# SPHEREview container: FastAPI backend + static frontend on one port.
# Works on any Docker host; Hugging Face Spaces (Docker SDK) expects port 7860.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=7860
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend backend
COPY config config
COPY frontend frontend

# The disk cache lives in backend/cache; make it writable for non-root hosts.
RUN mkdir -p backend/cache && chmod -R 777 backend/cache

EXPOSE 7860
CMD ["sh", "-c", "uvicorn backend.app:app --host 0.0.0.0 --port ${PORT} --timeout-graceful-shutdown 5"]
