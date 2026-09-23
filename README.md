# Sport Rental — прокат спортивного инвентаря

Учебный проект по DDD и чистой архитектуре: **6 самостоятельных REST-микросервисов, 13 агрегатов**.
Python 3.13+, FastAPI, Pydantic, SQLite, pytest. Каждый сервис имеет собственные
`pyproject.toml`, Dockerfile, пакет Python, HTTP-приложение и базу данных.

## Сервисы

| Проект | Ограниченный контекст | Агрегаты / REST-ресурсы | Swagger после запуска |
|---|---|---|---|
| `services/catalog` | Каталог | Category (`categories`), EquipmentModel (`models`) | http://localhost:8001/docs |
| `services/inventory` | Учёт инвентаря | RentalPoint (`points`), InventoryItem (`items`), Transfer (`transfers`) | http://localhost:8002/docs |
| `services/rental` | Аренда | Tariff (`tariffs`), Booking (`bookings`), RentalContract (`contracts`) | http://localhost:8003/docs |
| `services/customers` | Работа с клиентами | Customer (`customers`) | http://localhost:8004/docs |
| `services/billing` | Расчёты | Payment (`payments`), Deposit (`deposits`) | http://localhost:8005/docs |
| `services/maintenance` | Обслуживание | ServiceOrder (`orders`), DamageReport (`damage-reports`) | http://localhost:8006/docs |

## Быстрый запуск без Docker

В терминале из корня проекта:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python scripts/run_local.py
```

Скрипт запускает шесть отдельных процессов Uvicorn. Ctrl+C останавливает их все.
Базы сохраняются в `data/`. После запуска откройте Swagger по адресам из таблицы.
Для демонстрации в другом терминале, из корня проекта:

```bash
.venv/bin/python scripts/demo.py
```

Скрипт создаёт учебные данные для всех 13 типов агрегатов и выполняет операции
бронирования, оплаты, возврата, перемещения и обслуживания. Его можно запускать повторно:
он создаёт новый набор данных. Финансовые операции только учитываются локально;
реальные банковские списания не выполняются.

## Запуск через Docker Compose

Сначала запустите Docker Desktop или другой совместимый Docker daemon.

```bash
docker compose up --build -d
docker compose ps
```

Каждый контейнер слушает порт 8000, снаружи сервисы доступны на портах 8001–8006.
Порты опубликованы только на `127.0.0.1`. База каждого сервиса хранится в отдельном
именованном томе. Остановка с сохранением данных:

```bash
docker compose down
```

## Запуск отдельного проекта в PyCharm

Можно открыть корневую папку либо любой каталог `services/<имя>` как отдельный проект.
Для одного сервиса создайте интерпретатор Python 3.13+ и установите пакет из его каталога:

```bash
pip install -e .
uvicorn catalog_service.main:app --reload --port 8001
```

Здесь показан `catalog`; точные команды для остальных сервисов приведены в их README.
Для Run Configuration в PyCharm используйте Module name `uvicorn`, Parameters
`catalog_service.main:app --reload --port 8001`, Working directory `services/catalog`.
Для индивидуального запуска путь базы задаётся переменной окружения `DATABASE_PATH`.
По умолчанию это `data/<имя>.sqlite3` относительно рабочей папки.

## Чистая архитектура

```text
services/catalog/
├── pyproject.toml
├── Dockerfile
├── README.md
└── src/catalog_service/
    ├── domain/
    │   ├── entities.py       # агрегаты и поведение
    │   ├── values.py         # объекты-значения и проверки
    │   └── errors.py         # бизнес-ошибки
    ├── application/
    │   ├── ports.py          # интерфейсы Repository и UnitOfWork
    │   └── use_cases.py      # сценарии использования
    ├── infrastructure/
    │   └── sqlite.py         # хранение и транзакции
    ├── presentation/
    │   ├── schemas.py        # входные DTO и валидация REST
    │   └── routes.py         # HTTP-обработчики
    └── main.py               # связывание реализаций и запуск
```

Одинаковая структура используется во всех шести проектах.

Направление зависимостей:

```text
presentation → application → domain
infrastructure → application (порты), domain
main → все слои (composition root)
```

`domain` использует только стандартную библиотеку Python. `application` не импортирует
FastAPI, SQLite или другие внешние адаптеры. Репозиторий и транзакция внедряются через
`UnitOfWork`. HTTP-слой проверяет форму запроса, вызывает сценарий и преобразует результат
в JSON. Агрегаты содержат правила переходов состояния и проверки своих значений.
Изменения нескольких агрегатов внутри одного сервиса выполняются атомарно.

Каждый сервис владеет своей SQLite-базой. Другие сервисы не читают её и не импортируют
его Python-код. Связи между контекстами представлены UUID. Подробности:
[docs/architecture.md](docs/architecture.md).

## REST API

Префикс ресурсов: `/api/v1`. Для каждого ресурса реализованы:

- `POST /api/v1/<resource>` — создание;
- `GET /api/v1/<resource>` — список;
- `GET /api/v1/<resource>/{id}` — получение по UUID.

Дополнительные бизнес-операции:

| Сервис | Метод и путь после `/api/v1` | Тело |
|---|---|---|
| catalog | `POST /models/{id}/unpublish` | — |
| inventory | `PATCH /items/{id}/status` | `{"status":"rented"}` (`available`, `rented`, `maintenance`) |
| inventory | `POST /transfers/{id}/complete` | — |
| customers | `POST /customers/{id}/block` | `{"reason":"Нарушение условий"}` |
| customers | `POST /customers/{id}/unblock` | — |
| rental | `POST /bookings/{id}/cancel` | — |
| rental | `POST /contracts/{id}/close` | — |
| billing | `POST /payments/{id}/confirm` | — |
| billing | `POST /payments/{id}/refunds` | `{"amount":10000}` |
| billing | `POST /deposits/{id}/settlements` | `{"amount":10000,"kind":"return"}` или `kind=withhold` с `reason` |
| maintenance | `POST /orders/{id}/complete` | `{"result":"Работы выполнены"}` |

Деньги передаются целым числом **копеек**, валюта учебной версии — RUB.
Даты — ISO 8601 с часовым поясом, например `2027-01-01T12:00:00+04:00`.
Интервал аренды полуоткрытый: `[start, end)`, соседние интервалы допустимы.
Стоимость равна суточной ставке × количеству начатых суток × количеству экземпляров.
Сумма фиксируется в бронировании и переносится в договор.

Ответы: `201` — создание, `200` — чтение или действие, `404` — объект не найден,
`409` — конфликт состояния, `422` — некорректный запрос или нарушение правила значения.
Общий пример создания категории:

```bash
curl -X POST http://localhost:8001/api/v1/categories \
  -H 'Content-Type: application/json' \
  -d '{"name":"Велосипеды"}'
```

Полные схемы запросов/ответов доступны в Swagger и `/openapi.json` каждого сервиса.
Удаление истории и произвольное редактирование статусов не добавлены: изменения
выполняются через явные бизнес-операции.

## Проверки

```bash
python -m pytest
ruff check .
ruff format --check .
docker compose config --quiet
```

Проверяются REST API всех сервисов, сохранение данных после пересоздания приложения,
конкурентное бронирование, границы интервалов, откат транзакции при частично выполненном
перемещении, лимиты денежных операций и направление зависимостей слоёв.

При подготовке проекта: **18 тестов прошли на Python 3.14.3**; пройден HTTP-сценарий
через шесть реальных процессов; конфигурация Compose валидна. Контейнерная сборка
не запускалась: Docker daemon был выключен. Возможное предупреждение Starlette
об устаревании httpx в TestClient не влияет на результат тестов.

## Границы учебной реализации

Это работающие самостоятельные сервисы с базовыми сценариями, а не полная промышленная
система. Внешние UUID проверяются по формату, но **не запрашиваются у соседних сервисов**.
Например, rental пока не проверяет блокировку клиента или техническое состояние
оборудования; закрытие договора само по себе не меняет статус в inventory.
Демонстрационный скрипт явно выполняет связанные запросы.

Автоматическое взаимодействие через HTTP-адаптеры или события, outbox/inbox, саги,
авторизация, платёжный провайдер, автоматическое истечение резервов и пагинация —
следующие этапы. API не следует публиковать в интернет без авторизации.
В текущей модели один договор создаётся из одного бронирования и закрывается целиком.
Детальные позиции актов и работ, вложения и частичный возврат инвентаря упрощены.

SQLite хранит JSON-снимки агрегатов и сериализует команды через `BEGIN IMMEDIATE`.
Это обеспечивает атомарность локальных проверок, но ограничивает производительность:
для масштабирования потребуется отдельная СУБД каждого сервиса и миграции схемы.

Подход к разделению HTTP-маршрутов использует
[официальную документацию FastAPI](https://fastapi.tiangolo.com/tutorial/bigger-applications/).
