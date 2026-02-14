# Fair Sber Price

Единый актуальный документ по проекту.

## 1) Текущее состояние проекта

Проект работает в формате **bot-only**:
- основной интерфейс: Telegram-бот;
- веб-часть Django/Nginx исключена из рабочего прод-режима;
- legacy-веб код сохранен в репозитории на случай возврата.

Бот показывает справедливую оценку акций Сбера по модели P/B и объясняющие материалы.

## 2) Функциональность бота

Команды:
- `/start` — приветствие, меню кнопок, текущие данные;
- `/info` — текущая оценка;
- `/thesis` — инвестиционный тезис;
- `/method` — почему P/B = 1;
- `/range` — почему диапазон 1.0–1.2;
- `/risks` — ключевые риски;
- `/help` — справка.

Что рассчитывается:
- цена акции с MOEX;
- справедливая цена (капитал / количество акций);
- диапазон справедливой цены (+20%);
- P/B;
- вербальная оценка: дешево / справедливо / чуть дорого / дорого.

## 3) Архитектура

- `fsp/price/services.py` — бизнес-логика, интеграции MOEX + ЦБ РФ, кэширование;
- `fsp/telegrambot/bot.py` — Telegram handlers и UI;
- Django используется как каркас проекта + management commands + простая SQLite для служебных таблиц.

Данные:
- MOEX ISS API — рыночная цена;
- ЦБ РФ — собственный капитал банка.

## 4) Производительность и устойчивость

В сервисе реализовано:
- failover MOEX по базовым URL (`https` -> `http`);
- ограничение общего времени поиска цены MOEX;
- настраиваемые timeout/retry для MOEX и ЦБ;
- fallback кэш для последней доступной MOEX цены.

Это снижает зависание `/info` при сетевых проблемах.

## 5) Переменные окружения

Обязательные:
- `SECRET_KEY`
- `TELEGRAM_BOT_TOKEN`

Ключевые:
- `DEBUG=False`
- `BOT_ONLY_MODE=True`
- `ALLOWED_HOSTS` (для prod Django-конфига)

Параметры расчета:
- `SBER_STOCKS_QUANTITY`
- `CBR_BASE_URL`

Кэш:
- `CACHE_TIMEOUT`

MOEX/CBR network tuning:
- `MOEX_BASE_URLS=https://iss.moex.com,http://iss.moex.com`
- `MOEX_REQUEST_TIMEOUT=4`
- `MOEX_RETRIES=1`
- `MOEX_MAX_TOTAL_SECONDS=12`
- `CBR_REQUEST_TIMEOUT=8`
- `CBR_RETRIES=2`

Эталон — `.env.example`.

## 6) Локальный запуск

```bash
# из корня репозитория
cd fsp
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env
python manage.py migrate
python manage.py runtelegrambot
```

## 7) Продакшн запуск

Основной compose-файл (текущий):
- `docker-compose.prod.yml` — только Telegram-бот.

Запуск:
```bash
docker compose -f docker-compose.prod.yml up -d
```

Проверка:
```bash
docker compose -f docker-compose.prod.yml ps
docker logs fsp_telegram_bot --tail 200
```

## 8) Возврат legacy-веба (при необходимости)

Для восстановления веб-режима используйте `docker-compose.web-archive.yml` как основу.

Что нужно сделать:
1. Подготовить compose с `web + nginx` (можно отталкиваться от `docker-compose.web-archive.yml`).
2. Установить `BOT_ONLY_MODE=False` для web-сервиса.
3. Проверить маршруты и healthcheck веба.

## 9) Диагностика типовых проблем

### Бот долго отвечает на `/info`
Причина обычно в timeout к MOEX/ЦБ.

Что делать:
1. Проверить сетевую доступность `iss.moex.com` из контейнера.
2. Уменьшить `MOEX_REQUEST_TIMEOUT` и/или `MOEX_MAX_TOTAL_SECONDS`.
3. Проверить, что задан `MOEX_BASE_URLS` с HTTPS первым.
4. Посмотреть логи контейнера.

### Бот не запускается
Проверьте:
- `TELEGRAM_BOT_TOKEN` задан;
- контейнер поднялся без crash loop;
- нет конфликтов старых копий бота.

## 10) Что оставлено за рамками текущей версии

В текущем bot-only режиме отсутствуют:
- активный веб-интерфейс для пользователей;
- PostgreSQL/Redis/история снапшотов;
- `/history` и связанная историческая аналитика.

## 11) Полезные команды

```bash
# Django проверки
cd fsp && python manage.py check
cd fsp && python manage.py test

# Docker

docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f telegram-bot
```
