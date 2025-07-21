# Исправление проблемы с базой данных SQLite 🗄️

## 🚨 Проблема
```
django.db.utils.OperationalError: unable to open database file
sqlite3.OperationalError: unable to open database file
```

Django не мог открыть файл базы данных SQLite из-за проблем с правами доступа:
- Файл базы данных не существовал или имел неправильные права
- Пользователь `django` в контейнере не мог создать/изменить файл базы данных
- Миграции не могли выполниться из-за отсутствия доступа к БД

## ✅ Исправления

### 1. **Dockerfile.web** - создание БД с правильными правами
```dockerfile
# Создание директорий и файла БД с правильными правами
RUN mkdir -p logs staticfiles && \
    touch /app/db.sqlite3 && \
    chmod 664 /app/db.sqlite3 && \
    chown -R django:django /app

# Сбор статических файлов
RUN DJANGO_SETTINGS_MODULE=fsp.production python manage.py collectstatic --noinput

# Обеспечение правильных прав после collectstatic
RUN chown -R django:django /app/logs /app/staticfiles /app/db.sqlite3

# Переключение на непривилегированного пользователя
USER django
```

### 2. **Dockerfile.bot** - аналогичные исправления для бота
```dockerfile
# Создание директорий и файла БД с правильными правами
RUN mkdir -p logs && \
    touch /app/db.sqlite3 && \
    chmod 664 /app/db.sqlite3 && \
    chown -R django:django /app && \
    chmod 755 /app/logs

# Переключение на непривилегированного пользователя
USER django

# Запуск с миграциями
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py runtelegrambot"]
```

### 3. **scripts/fix_permissions.sh** - улучшена проверка БД
```bash
# Создание базы данных если её нет
if [ ! -f "fsp/db.sqlite3" ]; then
    echo "📝 Создание базы данных..."
    touch fsp/db.sqlite3
fi
chmod 664 fsp/db.sqlite3

# Тест записи в базу данных
if [ -w "fsp/db.sqlite3" ]; then
    echo "✅ База данных доступна для записи"
else
    echo "⚠️ Исправление прав на базу данных..."
    chmod 664 fsp/db.sqlite3
    chown 1000:1000 fsp/db.sqlite3
fi
```

## 🔍 Диагностика проблем с базой данных

### Проверка файла БД на сервере:
```bash
# Проверка существования и прав
ls -la /opt/fair-sber-price/fsp/db.sqlite3

# Проверка владельца (должен быть 1000:1000)
stat /opt/fair-sber-price/fsp/db.sqlite3

# Тест записи
touch /opt/fair-sber-price/fsp/db.sqlite3
echo "test" >> /opt/fair-sber-price/fsp/db.sqlite3
```

### Проверка в контейнере:
```bash
# Проверка доступа к БД в контейнере
docker exec fsp_web ls -la /app/db.sqlite3
docker exec fsp_web sqlite3 /app/db.sqlite3 ".tables"

# Тест Django подключения
docker exec fsp_web python manage.py check --database default
docker exec fsp_web python manage.py showmigrations
```

### Проверка миграций:
```bash
# Статус миграций
docker exec fsp_web python manage.py showmigrations

# Применение миграций
docker exec fsp_web python manage.py migrate --noinput
```

## 🚀 Применение исправлений

### Автоматически (рекомендуется):
```bash
git add .
git commit -m "Fix SQLite database permissions and creation"
git push origin main
```

GitHub Actions автоматически:
1. Пересоберет образы с правильным созданием БД
2. Настроит права доступа на сервере
3. Перезапустит контейнеры с рабочей БД

### Вручную на сервере:
```bash
# Подключение к серверу
ssh root@your-server-ip

# Запуск скрипта исправления
cd /opt/fair-sber-price
./scripts/fix_permissions.sh
```

## 📊 Проверка результата

После применения исправлений:

### 1. Проверка статуса контейнеров:
```bash
$ docker-compose -f docker-compose.prod.yml ps
NAME                STATUS
fsp_web             Up X minutes (healthy)
fsp_telegram_bot    Up X minutes (healthy)
fsp_redis           Up X minutes (healthy)
```

### 2. Проверка логов (без ошибок БД):
```bash
$ docker logs fsp_web --tail=10
[INFO] Starting gunicorn 21.2.0
[INFO] Listening at: http://0.0.0.0:8000
[INFO] Booting worker with pid: 6
# Без ошибок OperationalError
```

### 3. Проверка health endpoint:
```bash
$ curl http://localhost:8000/api/health/
{
  "status": "healthy",
  "checks": {
    "database": "ok"  # Должно быть "ok"
  }
}
```

### 4. Проверка главной страницы:
```bash
$ curl -I http://localhost:8000/
HTTP/1.1 200 OK  # Должно быть 200, не 404
```

## 🔧 Если проблемы с БД остаются

### 1. Проверьте права на файл БД:
```bash
ls -la /opt/fair-sber-price/fsp/db.sqlite3
# Должно быть: -rw-rw-r-- 1 1000 1000
```

### 2. Пересоздайте файл БД:
```bash
cd /opt/fair-sber-price
rm -f fsp/db.sqlite3
touch fsp/db.sqlite3
chmod 664 fsp/db.sqlite3
chown 1000:1000 fsp/db.sqlite3
```

### 3. Перезапустите контейнеры:
```bash
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

### 4. Примените миграции вручную:
```bash
docker exec fsp_web python manage.py migrate --noinput
```

## ✅ Ожидаемый результат

После исправлений:
- 🟢 База данных SQLite создается с правильными правами
- 🟢 Django может подключаться к БД без ошибок
- 🟢 Миграции применяются успешно
- 🟢 Веб-приложение отображает главную страницу (200 OK)
- 🟢 Telegram бот запускается без ошибок БД
- 🟢 Health check показывает "database": "ok"

## 📞 Поддержка

Если проблемы с базой данных продолжаются:
1. Запустите `./scripts/fix_permissions.sh`
2. Соберите логи: `docker logs fsp_web > db_error_logs.txt`
3. Проверьте права: `ls -la /opt/fair-sber-price/fsp/db.sqlite3`
4. Создайте Issue в GitHub с логами и информацией о правах

---

**База данных SQLite теперь работает корректно с правильными правами доступа!** 🗄️✅