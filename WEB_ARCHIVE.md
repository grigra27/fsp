# Web archive note

Проект переведен в режим **bot-only**.

- Веб-код (Django views/templates, nginx-конфиги, Dockerfile.web) сохранен в репозитории как legacy.
- Продакшн-компоновка `docker-compose.prod.yml` запускает только Telegram-бота.
- Архивная компоновка web+nginx сохранена в `docker-compose.web-archive.yml`.

## Как вернуть веб в будущем

1. Использовать `docker-compose.web-archive.yml` как основу для нового прод-файла.
2. Выставить `BOT_ONLY_MODE=False` в окружении web-сервиса.
3. Проверить маршруты и healthcheck веба, затем включить nginx.
