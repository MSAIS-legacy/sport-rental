# rental

Самостоятельный пакет микросервиса, REST-порт 8003, Swagger: http://localhost:8003/docs.

Внутри `src/rental_service`: domain, application, infrastructure, presentation и main.py.
Сервис владеет отдельной PostgreSQL-базой `rental`. Внешние адаптеры общей технической
библиотеки подключаются только на внешних слоях чистой архитектуры.

Запуск из корня репозитория: `docker compose up -d --build rental`.
Для полной системы и saga используйте `docker compose up -d --build`.
Подготовка .env, ключей JWT, локальная разработка и тесты описаны
в [корневом README](../../README.md).

Пакет для локальной разработки: `pip install -e packages/runtime -e services/rental`
из корня репозитория. В PyCharm используйте интерпретатор общей `.venv`.
