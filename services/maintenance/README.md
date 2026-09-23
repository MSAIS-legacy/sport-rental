# maintenance

Самостоятельный пакет микросервиса, REST-порт 8006, Swagger: http://localhost:8006/docs.

Внутри `src/maintenance_service`: domain, application, infrastructure, presentation и main.py.
Сервис владеет отдельной PostgreSQL-базой `maintenance`. Внешние адаптеры общей технической
библиотеки подключаются только на внешних слоях чистой архитектуры.

Запуск из корня репозитория: `docker compose up -d --build maintenance`.
Для полной системы и saga используйте `docker compose up -d --build`.
Подготовка .env, ключей JWT, локальная разработка и тесты описаны
в [корневом README](../../README.md).

Пакет для локальной разработки: `pip install -e packages/runtime -e services/maintenance`
из корня репозитория. В PyCharm используйте интерпретатор общей `.venv`.
