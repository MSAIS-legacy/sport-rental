FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY packages/runtime /tmp/runtime
COPY services/maintenance /tmp/service
RUN pip install --no-cache-dir /tmp/runtime /tmp/service && useradd --uid 10001 --create-home appuser
USER appuser
EXPOSE 8000
CMD ["uvicorn", "maintenance_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
