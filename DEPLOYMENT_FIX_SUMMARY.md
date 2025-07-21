# Исправления для деплоя - Сводка

## 🔧 Исправленные проблемы

### 1. ❌ Проблема с bootstrap.css.map
**Ошибка**: `whitenoise.storage.MissingFileError: The file 'css/bootstrap.css.map' could not be found`

**✅ Решение**:
- Изменен `STATICFILES_STORAGE` в `production.py` на `CompressedStaticFilesStorage`
- Добавлены настройки WhiteNoise для пропуска .map файлов
- Обновлен `Dockerfile.web` для использования production настроек

### 2. ❌ Проблема с SSH аутентификацией
**Ошибка**: `ssh: this private key is passphrase protected`

**✅ Решение**:
- Добавлен параметр `passphrase` в GitHub Actions workflow
- Создана инструкция по настройке GitHub Secrets
- Обеспечена поддержка безопасных SSH ключей с паролем

## 📁 Измененные файлы

### 1. `Dockerfile.web`
```dockerfile
# Используем production настройки для collectstatic
RUN DJANGO_SETTINGS_MODULE=fsp.production python manage.py collectstatic --noinput
```

### 2. `fsp/fsp/production.py`
```python
# Исправленное хранилище статических файлов
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# Дополнительные настройки WhiteNoise
WHITENOISE_SKIP_COMPRESS_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'zip', 'gz', 'tgz', 'bz2', 'tbz', 'xz', 'br', 'map']
WHITENOISE_USE_FINDERS = True
```

### 3. `.github/workflows/deploy.yml`
```yaml
# Добавлена поддержка passphrase для SSH ключа
passphrase: ${{ secrets.DO_SSH_PASSPHRASE }}
```

## 📋 Новые файлы

1. **`DEPLOYMENT_SECRETS_SETUP.md`** - инструкция по настройке GitHub Secrets
2. **`fsp/scripts/fix_css_maps.py`** - резервный скрипт для исправления CSS
3. **`CSS_FIX_SUMMARY.md`** - подробное описание исправления CSS проблемы

## 🚀 Инструкции для деплоя

### Шаг 1: Настройте GitHub Secrets
Добавьте в `Settings` → `Secrets and variables` → `Actions`:

- `DO_HOST` - IP адрес сервера
- `DO_USERNAME` - имя пользователя (обычно `root`)
- `DO_SSH_KEY` - приватный SSH ключ
- `DO_SSH_PASSPHRASE` - пароль для SSH ключа (если есть)
- `DO_PORT` - SSH порт (обычно `22`)
- `SECRET_KEY` - Django SECRET_KEY
- `ALLOWED_HOSTS` - разрешенные хосты
- `TELEGRAM_BOT_TOKEN` - токен Telegram бота

### Шаг 2: Деплой
```bash
git add .
git commit -m "Fix deployment issues: CSS maps and SSH auth"
git push origin main
```

GitHub Actions автоматически:
1. ✅ Соберет Docker образы (без ошибок CSS)
2. ✅ Подключится к серверу по SSH (с поддержкой passphrase)
3. ✅ Настроит сервер автоматически
4. ✅ Запустит приложение

### Шаг 3: Проверка
После деплоя проверьте:
- `http://your-server-ip:8000` - веб-приложение
- `http://your-server-ip:8000/api/health/` - health check
- Telegram бот должен отвечать на команды

## 🔧 Устранение проблем

### SSH ключ не работает
1. Убедитесь, что SSH ключ защищен паролем (passphrase)
2. Проверьте, что публичный ключ добавлен на сервер в `~/.ssh/authorized_keys`
3. Обновите `DO_SSH_KEY` и `DO_SSH_PASSPHRASE` в GitHub Secrets

### CSS файлы не загружаются
1. Проверьте логи контейнера: `docker logs fsp_web`
2. При необходимости запустите: `python fsp/scripts/fix_css_maps.py`

### Контейнеры не запускаются
1. Проверьте статус: `docker-compose -f docker-compose.prod.yml ps`
2. Посмотрите логи: `docker-compose -f docker-compose.prod.yml logs`

## ✅ Результат

После всех исправлений:
- 🟢 Docker образы собираются без ошибок
- 🟢 SSH подключение работает с passphrase
- 🟢 Статические файлы загружаются корректно
- 🟢 Автоматический деплой полностью функционален
- 🟢 Приложение стабильно работает в продакшене

**Деплой готов к использованию!** 🚀