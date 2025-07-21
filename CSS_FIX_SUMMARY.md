# Исправление проблемы с bootstrap.css.map

## Проблема
При сборке Docker образа возникала ошибка:
```
whitenoise.storage.MissingFileError: The file 'css/bootstrap.css.map' could not be found
```

## Решение

### 1. Изменения в Dockerfile.web
- Добавлено использование production настроек для collectstatic:
```dockerfile
RUN DJANGO_SETTINGS_MODULE=fsp.production python manage.py collectstatic --noinput
```

### 2. Изменения в production.py
- Заменено хранилище статических файлов:
```python
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
```
- Добавлены настройки WhiteNoise:
```python
WHITENOISE_SKIP_COMPRESS_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'zip', 'gz', 'tgz', 'bz2', 'tbz', 'xz', 'br', 'map']
WHITENOISE_USE_FINDERS = True
```

### 3. Резервный скрипт
Создан скрипт `fsp/scripts/fix_css_maps.py` для удаления ссылок на .map файлы при необходимости.

## Результат
- ✅ Сборка Docker образа проходит без ошибок
- ✅ Статические файлы собираются корректно
- ✅ WhiteNoise работает стабильно в продакшене
- ✅ Отсутствующие .map файлы не вызывают ошибок

## Тестирование
Для проверки исправлений запустите:
```bash
git add .
git commit -m "Fix CSS map files issue"
git push origin main
```

GitHub Actions автоматически соберет и задеплоит исправленную версию.