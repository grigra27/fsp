# Telegram Bot for Fair Sber Price Project

## Описание
Этот бот отправляет данные, аналогичные отображаемым на главной странице сайта (функция index из price/views.py), в ответ на команды Telegram `/start` или `/info`.

## Установка зависимостей

```bash
pip install -r requirements.txt
```

## Настройка переменных окружения

Перед запуском необходимо указать токен Telegram-бота:

```bash
export TELEGRAM_BOT_TOKEN=ваш_токен_бота
```

## Запуск бота

```bash
python manage.py runtelegrambot
```

## Где находится код
- Основная логика бота: `fsp/telegrambot/bot.py`
- Django management команда: `fsp/telegrambot/management/commands/runtelegrambot.py`

## Что делает бот
Бот поддерживает команды `/start`, `/info`, `/thesis`, `/method`, `/range`, `/risks`, `/help`.

Команды `/start` и `/info` отправляют данные:
- MOEX цена
- Справедливая цена
- Справедливая цена +20%
- Оценка цены

Дополнительно бот отправляет:
- Инвестиционный тезис
- Пояснение методологии P/B = 1
- Пояснение диапазона P/B 1.0-1.2
- Ключевые риски

## Примечания
- Для работы бота требуется интернет-доступ и корректные функции в `price/views.py`.
- Если потребуется добавить новые команды — расширяйте файл `bot.py`.
