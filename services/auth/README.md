# auth

Самостоятельный пакет микросервиса, REST-порт 8007, Swagger: http://localhost:8007/docs.

Внутри `src/auth_service`: domain, application, infrastructure, presentation и main.py.
Сервис владеет отдельной PostgreSQL-базой `auth`. Внешние адаптеры общей технической
библиотеки подключаются только на внешних слоях чистой архитектуры.

Запуск из корня репозитория: `docker compose up -d --build auth`.
Для полной системы и saga используйте `docker compose up -d --build`.
Подготовка .env, ключей JWT, локальная разработка и тесты описаны
в [корневом README](../../README.md).

Пакет для локальной разработки: `pip install -e packages/runtime -e services/auth`
из корня репозитория. В PyCharm используйте интерпретатор общей `.venv`.
