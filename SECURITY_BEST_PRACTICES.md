# Безопасность деплоя - Лучшие практики

## 🔐 SSH Безопасность

### ✅ Обязательные требования:
- **SSH ключи ДОЛЖНЫ быть защищены паролем (passphrase)**
- **Используйте современные алгоритмы**: `ed25519` или `rsa` (минимум 4096 бит)
- **Никогда не используйте ключи без пароля** для продакшн серверов

### 🔑 Генерация безопасного SSH ключа:
```bash
# Рекомендуемый способ - ed25519 с паролем
ssh-keygen -t ed25519 -C "github-actions-deploy-$(date +%Y%m%d)"

# Альтернативный способ - RSA 4096 бит
ssh-keygen -t rsa -b 4096 -C "github-actions-deploy-$(date +%Y%m%d)"

# ВАЖНО: При запросе passphrase введите НАДЕЖНЫЙ пароль!
# Минимум 12 символов, включая буквы, цифры и спецсимволы
```

### 🛡️ Настройка сервера:
```bash
# Правильные права доступа
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
chmod 600 ~/.ssh/id_*

# Отключение входа по паролю (только ключи)
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart sshd
```

## 🔒 Django Безопасность

### SECRET_KEY
```python
# Генерация надежного SECRET_KEY
import secrets
secret_key = secrets.token_urlsafe(50)
print(f"SECRET_KEY={secret_key}")
```

### Переменные окружения
- **Никогда не коммитьте секреты в Git**
- **Используйте GitHub Secrets** для всех чувствительных данных
- **Регулярно ротируйте ключи** (каждые 3-6 месяцев)

## 🚫 Что НЕ делать

### ❌ Небезопасные практики:
- SSH ключи без passphrase
- Хранение секретов в коде
- Использование слабых паролей
- Открытые порты без необходимости
- Запуск сервисов от root пользователя

### ❌ Небезопасные команды:
```bash
# НЕ ДЕЛАЙТЕ ТАК:
ssh-keygen -t rsa -N ""  # Ключ без пароля
chmod 777 ~/.ssh         # Слишком открытые права
```

## ✅ Рекомендуемая конфигурация

### GitHub Secrets (все обязательны):
```
DO_HOST=your-server-ip
DO_USERNAME=root
DO_SSH_KEY=-----BEGIN OPENSSH PRIVATE KEY-----...
DO_SSH_PASSPHRASE=your-strong-passphrase
DO_PORT=22
SECRET_KEY=your-50-char-secret-key
ALLOWED_HOSTS=your-domain.com,your-server-ip
TELEGRAM_BOT_TOKEN=your-bot-token
```

### Файрвол сервера:
```bash
# Настройка UFW (рекомендуется)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 8000/tcp  # Приложение
sudo ufw --force enable
```

## 🔄 Регулярное обслуживание

### Каждые 3 месяца:
- [ ] Ротация SSH ключей
- [ ] Обновление SECRET_KEY
- [ ] Проверка логов безопасности
- [ ] Обновление системы сервера

### Каждый месяц:
- [ ] Проверка активных SSH сессий
- [ ] Анализ логов доступа
- [ ] Обновление зависимостей

## 🚨 Реагирование на инциденты

### При компрометации SSH ключа:
1. **Немедленно** удалите ключ с сервера
2. Сгенерируйте новый ключ с новым паролем
3. Обновите GitHub Secrets
4. Проверьте логи на подозрительную активность

### При компрометации SECRET_KEY:
1. Сгенерируйте новый SECRET_KEY
2. Обновите GitHub Secret
3. Перезапустите приложение
4. Проверьте сессии пользователей

## 📊 Мониторинг

### Логи для отслеживания:
- SSH подключения: `/var/log/auth.log`
- Приложение: `fsp/logs/app.log`
- Системные события: `/var/log/syslog`

### Команды для проверки:
```bash
# Активные SSH сессии
who

# Последние входы
last

# Неудачные попытки входа
sudo grep "Failed password" /var/log/auth.log
```

---

**Помните**: Безопасность - это процесс, а не состояние. Регулярно обновляйте и проверяйте свои настройки безопасности! 🛡️