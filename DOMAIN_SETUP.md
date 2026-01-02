# Настройка домена onbr.site

## 1. Настройка у регистратора домена

### Если домен уже зарегистрирован:
1. Войдите в панель управления вашего регистратора (например, Namecheap, GoDaddy, REG.RU)
2. Найдите раздел "DNS Management" или "Управление DNS"
3. Настройте следующие DNS записи:

```
Тип    Имя        Значение              TTL
A      @          YOUR_DIGITALOCEAN_IP  300
A      www        YOUR_DIGITALOCEAN_IP  300
CNAME  www        onbr.site             300
```

### Если домен не зарегистрирован:
1. Зарегистрируйте домен `onbr.site` у любого регистратора
2. После регистрации выполните настройку DNS записей выше

## 2. Настройка DigitalOcean

### Получение IP адреса вашего дроплета:
```bash
# В панели DigitalOcean или через API
curl -X GET \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  "https://api.digitalocean.com/v2/droplets"
```

### Настройка DNS в DigitalOcean (опционально):
1. Войдите в панель DigitalOcean
2. Перейдите в раздел "Networking" → "Domains"
3. Добавьте домен `onbr.site`
4. Создайте записи:
   - A запись: `@` → IP вашего дроплета
   - A запись: `www` → IP вашего дроплета

### Обновление nameservers (если используете DNS DigitalOcean):
У регистратора домена измените nameservers на:
```
ns1.digitalocean.com
ns2.digitalocean.com
ns3.digitalocean.com
```

## 3. Обновление GitHub Secrets

В вашем GitHub репозитории обновите следующие secrets:

1. Перейдите в Settings → Secrets and variables → Actions
2. Обновите или добавьте:
```
ALLOWED_HOSTS=onbr.site,www.onbr.site,YOUR_DIGITALOCEAN_IP
```

## 4. Настройка SSL сертификатов

После того как DNS записи распространятся (обычно 1-24 часа), настройте SSL:

### Автоматическая настройка через Let's Encrypt:
```bash
# На сервере DigitalOcean
cd /opt/fair-sber-price

# Остановите nginx
docker-compose -f docker-compose.prod.yml stop nginx

# Получите сертификаты
docker run -it --rm \
  -v "$(pwd)/ssl_copy:/etc/letsencrypt" \
  -p 80:80 \
  certbot/certbot certonly --standalone \
  -d onbr.site -d www.onbr.site \
  --email ffred-drues@gmail.com \
  --agree-tos --non-interactive

# Скопируйте сертификаты в нужную директорию
mkdir -p ssl_copy
cp -r /etc/letsencrypt/* ssl_copy/ 2>/dev/null || true

# Запустите nginx обратно
docker-compose -f docker-compose.prod.yml up -d nginx
```

## 5. Проверка настройки

### Проверьте DNS:
```bash
# Проверка A записи
dig onbr.site A
dig www.onbr.site A

# Проверка доступности
ping onbr.site
```

### Проверьте сайт:
1. Откройте http://onbr.site - должен перенаправить на https
2. Откройте https://onbr.site - должен показать сайт
3. Проверьте https://onbr.site/api/health/ - должен вернуть статус OK

## 6. Автоматическое обновление сертификатов

Добавьте в crontab для автоматического обновления:
```bash
# Откройте crontab
crontab -e

# Добавьте строку (обновление каждые 3 месяца в 3:00)
0 3 1 */3 * cd /opt/fair-sber-price && docker run --rm -v "$(pwd)/ssl_copy:/etc/letsencrypt" -p 80:80 certbot/certbot renew --standalone --pre-hook "docker-compose -f docker-compose.prod.yml stop nginx" --post-hook "docker-compose -f docker-compose.prod.yml start nginx"
```

## Возможные проблемы и решения

### DNS не распространился:
- Подождите до 24 часов
- Проверьте через https://dnschecker.org/
- Убедитесь, что TTL установлен на 300 секунд

### SSL сертификат не получается:
- Убедитесь, что порт 80 открыт
- Проверьте, что nginx остановлен во время получения сертификата
- Убедитесь, что DNS записи указывают на правильный IP

### Сайт не открывается:
- Проверьте статус контейнеров: `docker-compose -f docker-compose.prod.yml ps`
- Проверьте логи: `docker logs fsp_nginx`
- Убедитесь, что ALLOWED_HOSTS содержит новый домен

## Финальная проверка

После завершения всех настроек:
1. ✅ https://onbr.site открывается
2. ✅ https://www.onbr.site открывается  
3. ✅ http://onbr.site перенаправляет на https
4. ✅ SSL сертификат валидный (зеленый замок в браузере)
5. ✅ API работает: https://onbr.site/api/current/
6. ✅ Health check: https://onbr.site/api/health/