# customers

Самостоятельный пакет микросервиса, REST-порт 8004, Swagger: http://localhost:8004/docs.

Внутри `src/customers_service`: domain, application, infrastructure, presentation и main.py.
Сервис владеет отдельной PostgreSQL-базой `customers`. Внешние адаптеры общей технической
библиотеки подключаются только на внешних слоях чистой архитектуры.

Запуск из корня репозитория: `docker compose up -d --build customers`.
Для полной системы и saga используйте `docker compose up -d --build`.
Подготовка .env, ключей JWT, локальная разработка и тесты описаны
в [корневом README](../../README.md).

Пакет для локальной разработки: `pip install -e packages/runtime -e services/customers`
из корня репозитория. В PyCharm используйте интерпретатор общей `.venv`.
