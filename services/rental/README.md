# Аренда

Самостоятельный микросервис `rental`, локальный порт `8003`.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn rental_service.main:app --reload --port 8003
```

Swagger: http://localhost:8003/docs, OpenAPI: `/openapi.json`.
Проверка запуска: `GET /health`. REST API: `/api/v1`.

База SQLite задаётся переменной `DATABASE_PATH`, по умолчанию `data/rental.sqlite3`.
Настоящий файл базы создаётся при первом обращении к данным.
Каждый сервис использует собственную базу и не импортирует код соседних сервисов.

- `domain`: агрегаты, объекты-значения, бизнес-правила и ошибки.
- `application`: сценарии использования и порты Repository / UnitOfWork.
- `infrastructure`: SQLite-реализация портов.
- `presentation`: REST-маршруты и входные DTO Pydantic.
- `main.py`: сборка зависимостей и обработчики ошибок.

Описание ограничений и общие инструкции: [корневой README](../../README.md).
