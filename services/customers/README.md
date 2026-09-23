# Работа с клиентами

Самостоятельный микросервис `customers`, локальный порт `8004`.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn customers_service.main:app --reload --port 8004
```

Swagger: http://localhost:8004/docs, OpenAPI: `/openapi.json`.
Проверка запуска: `GET /health`. REST API: `/api/v1`.

База SQLite задаётся переменной `DATABASE_PATH`, по умолчанию `data/customers.sqlite3`.
Настоящий файл базы создаётся при первом обращении к данным.
Каждый сервис использует собственную базу и не импортирует код соседних сервисов.

- `domain`: агрегаты, объекты-значения, бизнес-правила и ошибки.
- `application`: сценарии использования и порты Repository / UnitOfWork.
- `infrastructure`: SQLite-реализация портов.
- `presentation`: REST-маршруты и входные DTO Pydantic.
- `main.py`: сборка зависимостей и обработчики ошибок.

Описание ограничений и общие инструкции: [корневой README](../../README.md).
