FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DATABASE_PATH=/app/data/catalog.sqlite3
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir . && useradd --uid 10001 --create-home appuser && mkdir data && chown appuser:appuser data
USER appuser
EXPOSE 8000
CMD ["uvicorn", "catalog_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
