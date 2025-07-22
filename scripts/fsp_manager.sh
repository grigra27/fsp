#!/bin/bash

# Универсальный скрипт управления Fair Sber Price
# Использование: ./scripts/fsp_manager.sh [команда] [опции]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции вывода
info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; }

# Проверка директории проекта
check_project_dir() {
    if [[ ! -f "$PROJECT_DIR/docker-compose.prod.yml" ]]; then
        error "Не найден docker-compose.prod.yml. Убедитесь, что вы в директории проекта."
        exit 1
    fi
    cd "$PROJECT_DIR"
}

# Функция помощи
show_help() {
    echo "Fair Sber Price - Универсальный скрипт управления"
    echo ""
    echo "Использование: $0 [команда] [опции]"
    echo ""
    echo "Основные команды:"
    echo "  deploy      - Полный деплой приложения"
    echo "  start       - Запуск всех сервисов"
    echo "  stop        - Остановка всех сервисов"
    echo "  restart     - Перезапуск всех сервисов"
    echo "  status      - Статус контейнеров"
    echo "  logs        - Просмотр логов (опция: имя сервиса)"
    echo ""
    echo "Диагностика и исправление:"
    echo "  health      - Проверка здоровья приложения"
    echo "  fix         - Исправление частых проблем"
    echo "  fix-bot     - Исправление проблем с Telegram ботом"
    echo "  fix-perms   - Исправление прав доступа"
    echo "  debug-404   - Диагностика 404 ошибки"
    echo "  debug-bot   - Диагностика Telegram бота"
    echo "  debug-net   - Диагностика сетевых проблем"
    echo ""
    echo "Обслуживание:"
    echo "  update      - Обновление Docker образов"
    echo "  backup      - Резервная копия базы данных"
    echo "  clean       - Очистка неиспользуемых ресурсов"
    echo "  nginx       - Настройка и диагностика Nginx"
    echo ""
    echo "Примеры:"
    echo "  $0 deploy   # Полный деплой"
    echo "  $0 logs web # Логи веб-приложения"
    echo "  $0 debug-bot # Диагностика Telegram бота"
}

# Деплой приложения
deploy() {
    info "🚀 Начинаем деплой Fair Sber Price..."
    
    # Остановка контейнеров
    info "Остановка существующих контейнеров..."
    docker-compose -f docker-compose.prod.yml down || true
    
    # Создание .env если не существует
    if [[ ! -f .env ]]; then
        warning ".env файл не найден, создаем из примера..."
        cp .env.example .env
        warning "Отредактируйте .env файл с вашими настройками!"
        return 1
    fi
    
    # Исправление прав доступа
    info "Исправление прав доступа..."
    mkdir -p fsp/logs fsp/staticfiles ssl
    
    if [[ ! -f fsp/db.sqlite3 ]]; then
        touch fsp/db.sqlite3
    fi
    
    chmod 666 fsp/db.sqlite3
    chmod 755 fsp/logs fsp/staticfiles
    chown -R 1000:1000 fsp/ 2>/dev/null || true
    
    # Обновление образов
    info "Обновление Docker образов..."
    docker pull ghcr.io/grigra27/fair_sber_price-web:latest || warning "Не удалось обновить web образ"
    docker pull ghcr.io/grigra27/fair_sber_price-bot:latest || warning "Не удалось обновить bot образ"
    docker pull redis:7-alpine
    docker pull nginx:alpine
    
    # Запуск сервисов
    info "Запуск сервисов..."
    docker-compose -f docker-compose.prod.yml up -d
    
    # Ожидание запуска
    info "Ожидание запуска сервисов (30 секунд)..."
    sleep 30
    
    # Проверка статуса
    status
    health
    
    success "Деплой завершен!"
    info "Приложение доступно по адресу: http://$(hostname -I | awk '{print $1}')/"
}

# Запуск сервисов
start() {
    info "Запуск сервисов..."
    docker-compose -f docker-compose.prod.yml up -d
    success "Сервисы запущены"
}

# Остановка сервисов
stop() {
    info "Остановка сервисов..."
    docker-compose -f docker-compose.prod.yml down
    success "Сервисы остановлены"
}

# Перезапуск сервисов
restart() {
    info "Перезапуск сервисов..."
    docker-compose -f docker-compose.prod.yml restart
    success "Сервисы перезапущены"
}

# Статус контейнеров
status() {
    info "Статус контейнеров:"
    docker-compose -f docker-compose.prod.yml ps
}

# Просмотр логов
logs() {
    local service=${1:-""}
    if [[ -n "$service" ]]; then
        info "Логи сервиса $service:"
        docker logs "fsp_$service" --tail=50 -f
    else
        info "Логи всех сервисов:"
        docker-compose -f docker-compose.prod.yml logs --tail=20
    fi
}

# Проверка здоровья
health() {
    info "🏥 Проверка здоровья приложения..."
    
    # Проверка контейнеров
    local containers=$(docker-compose -f docker-compose.prod.yml ps --services)
    for container in $containers; do
        local status=$(docker inspect "fsp_$container" --format='{{.State.Status}}' 2>/dev/null || echo "not found")
        if [[ "$status" == "running" ]]; then
            success "$container: работает"
        else
            error "$container: $status"
        fi
    done
    
    # Проверка health endpoint
    info "Проверка health endpoint..."
    if curl -f http://localhost/api/health/ >/dev/null 2>&1; then
        success "Health endpoint: OK"
    elif curl -f http://localhost:8000/api/health/ >/dev/null 2>&1; then
        warning "Health endpoint: OK (через порт 8000)"
    else
        error "Health endpoint: недоступен"
    fi
    
    # Проверка Telegram бота
    info "Проверка Telegram бота..."
    local bot_logs=$(docker logs fsp_telegram_bot --tail=5 2>/dev/null | grep -i "error\|exception" || true)
    if [[ -z "$bot_logs" ]]; then
        success "Telegram бот: работает"
    else
        warning "Telegram бот: возможны проблемы"
    fi
    
    # Детальная информация о health check
    info "Детальная информация о health check:"
    curl -s http://localhost:8000/api/health/ | python3 -m json.tool 2>/dev/null || echo "Не удалось получить JSON ответ"
    
    # Проверка Docker health status
    info "Docker health status:"
    docker inspect fsp_web --format='{{.State.Health.Status}}' 2>/dev/null || echo "Health check не настроен"
}

# Исправление проблем
fix() {
    info "🔧 Исправление частых проблем..."
    
    # Остановка системного nginx
    if systemctl is-active --quiet nginx 2>/dev/null; then
        warning "Остановка системного nginx..."
        systemctl stop nginx
        systemctl disable nginx
    fi
    
    # Исправление прав доступа
    info "Исправление прав доступа..."
    chmod 666 fsp/db.sqlite3 2>/dev/null || true
    chmod 755 fsp/logs fsp/staticfiles 2>/dev/null || true
    chown -R 1000:1000 fsp/ 2>/dev/null || true
    
    # Настройка файрвола
    if command -v ufw >/dev/null 2>&1; then
        info "Настройка файрвола..."
        ufw allow 80/tcp >/dev/null 2>&1 || true
        ufw allow 443/tcp >/dev/null 2>&1 || true
        ufw allow 8000/tcp >/dev/null 2>&1 || true
    fi
    
    # Перезапуск сервисов
    restart
    
    success "Исправления применены"
}

# Исправление проблем с Telegram ботом
fix_bot() {
    info "🔧 Исправление проблем с Telegram ботом..."
    
    # Останавливаем бота
    info "Остановка бота..."
    docker-compose -f docker-compose.prod.yml stop telegram-bot
    
    # Удаляем старый контейнер
    info "Удаление старого контейнера..."
    docker-compose -f docker-compose.prod.yml rm -f telegram-bot
    
    # Обновляем образ бота
    info "Обновление образа бота..."
    docker pull ghcr.io/grigra27/fair_sber_price-bot:latest
    
    # Проверяем переменные окружения
    info "Проверка переменных окружения..."
    if [ -f .env ]; then
        source .env
    fi
    
    # Проверяем обязательные переменные
    missing_vars=""
    if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
        missing_vars="$missing_vars TELEGRAM_BOT_TOKEN"
    fi
    if [ -z "$SECRET_KEY" ]; then
        missing_vars="$missing_vars SECRET_KEY"
    fi
    if [ -z "$ALLOWED_HOSTS" ]; then
        missing_vars="$missing_vars ALLOWED_HOSTS"
    fi
    
    if [ -n "$missing_vars" ]; then
        error "Отсутствуют переменные окружения:$missing_vars"
        error "Проверьте файл .env"
        return 1
    fi
    
    success "Все необходимые переменные окружения найдены"
    
    # Проверяем доступность базы данных
    info "Проверка базы данных..."
    if [ ! -f "./fsp/db.sqlite3" ]; then
        warning "База данных не найдена, создаем..."
        touch ./fsp/db.sqlite3
        chmod 664 ./fsp/db.sqlite3
    fi
    
    # Создаем директорию для логов если её нет
    info "Создание директории для логов..."
    mkdir -p ./fsp/logs
    chmod 755 ./fsp/logs
    
    # Запускаем бота
    info "Запуск бота..."
    docker-compose -f docker-compose.prod.yml up -d telegram-bot
    
    # Ждем запуска
    info "Ожидание запуска бота..."
    sleep 10
    
    # Проверяем статус
    info "Проверка статуса бота..."
    docker-compose -f docker-compose.prod.yml ps telegram-bot
    
    # Показываем логи
    info "Последние логи бота:"
    docker logs fsp_telegram_bot --tail=20
    
    success "Исправление завершено!"
}

# Исправление прав доступа
fix_permissions() {
    info "🔧 Исправление прав доступа для контейнеров..."
    
    # Останавливаем все контейнеры
    info "Остановка контейнеров..."
    docker-compose -f docker-compose.prod.yml down
    
    # Создаем необходимые директории с правильными правами
    info "Создание директорий с правильными правами..."
    mkdir -p fsp/logs
    mkdir -p fsp/staticfiles
    chmod 755 fsp/logs
    chmod 755 fsp/staticfiles
    
    # Создаем базу данных если её нет
    info "Проверка базы данных..."
    if [ ! -f "fsp/db.sqlite3" ]; then
        info "Создание базы данных..."
        touch fsp/db.sqlite3
    fi
    chmod 664 fsp/db.sqlite3
    
    # Убеждаемся, что база данных доступна для записи
    info "Тест записи в базу данных..."
    if [ -w "fsp/db.sqlite3" ]; then
        success "База данных доступна для записи"
    else
        warning "Исправление прав на базу данных..."
        chmod 664 fsp/db.sqlite3
        chown 1000:1000 fsp/db.sqlite3
    fi
    
    # Устанавливаем правильные права на все файлы проекта
    info "Установка прав доступа..."
    chown -R 1000:1000 fsp/
    find fsp/ -type d -exec chmod 755 {} \;
    find fsp/ -type f -exec chmod 644 {} \;
    chmod 664 fsp/db.sqlite3
    chmod 755 fsp/logs
    chmod 755 fsp/staticfiles
    
    # Обновляем образы
    info "Обновление Docker образов..."
    docker pull ghcr.io/grigra27/fair_sber_price-web:latest
    docker pull ghcr.io/grigra27/fair_sber_price-bot:latest
    
    # Запускаем контейнеры
    info "Запуск контейнеров..."
    docker-compose -f docker-compose.prod.yml up -d
    
    # Ждем запуска
    info "Ожидание запуска сервисов..."
    sleep 30
    
    # Проверяем статус
    info "Проверка статуса контейнеров:"
    docker-compose -f docker-compose.prod.yml ps
    
    success "Исправление прав доступа завершено!"
}

# Диагностика 404 ошибки
debug_404() {
    info "🔍 Диагностика 404 ошибки на главной странице..."
    
    # Статус контейнеров
    info "Статус контейнеров:"
    docker-compose -f docker-compose.prod.yml ps
    
    info "Логи веб-приложения (последние 30 строк):"
    docker logs fsp_web --tail=30
    
    info "Тест главной страницы изнутри контейнера:"
    docker exec fsp_web curl -I http://localhost:8000/ 2>/dev/null || error "Не удалось подключиться изнутри контейнера"
    
    info "Тест с хоста:"
    curl -I http://localhost:8000/ 2>/dev/null || error "Не удалось подключиться с хоста"
    
    info "Проверка Django URL patterns:"
    docker exec fsp_web python manage.py show_urls 2>/dev/null || warning "Команда show_urls недоступна"
    
    info "Проверка Django приложений:"
    docker exec fsp_web python manage.py check
    
    info "Проверка статических файлов:"
    docker exec fsp_web ls -la /app/staticfiles/ | head -10
    
    info "Проверка шаблонов:"
    docker exec fsp_web ls -la /app/templates/
    
    info "Тест health endpoint:"
    curl -s http://localhost:8000/api/health/ | python3 -m json.tool 2>/dev/null || error "Health endpoint недоступен"
    
    info "Проверка переменных окружения:"
    docker exec fsp_web env | grep -E "(DEBUG|ALLOWED_HOSTS|DJANGO_SETTINGS_MODULE)" | sed 's/=.*/=***/'
    
    success "Диагностика завершена!"
}

# Диагностика Telegram бота
debug_bot() {
    info "🔍 Диагностика Telegram бота..."
    
    # Проверяем статус контейнеров
    info "Статус контейнеров:"
    docker-compose -f docker-compose.prod.yml ps
    
    info "Детальная информация о боте:"
    docker inspect fsp_telegram_bot --format='{{.State.Status}}: {{.State.Error}}'
    
    info "Последние логи бота:"
    docker logs fsp_telegram_bot --tail=50
    
    info "Проверка переменных окружения бота:"
    docker exec fsp_telegram_bot env | grep -E "(TELEGRAM_BOT_TOKEN|DJANGO_SETTINGS_MODULE|SECRET_KEY)" | sed 's/=.*/=***/'
    
    info "Проверка доступности базы данных:"
    docker exec fsp_telegram_bot python manage.py check
    
    info "Проверка Django приложений:"
    docker exec fsp_telegram_bot python manage.py showmigrations
    
    info "Тест подключения к Redis:"
    docker exec fsp_redis redis-cli ping
    
    info "Проверка сетевого подключения:"
    docker exec fsp_telegram_bot ping -c 3 redis
    
    success "Диагностика завершена!"
}

# Диагностика сетевых проблем
debug_network() {
    info "🌐 Диагностика сетевых проблем..."
    
    # Получаем информацию о сервере
    SERVER_IP=$(hostname -I | awk '{print $1}')
    DOMAIN="fsp.hopto.org"
    
    info "Информация о сервере:"
    echo "IP адрес: $SERVER_IP"
    echo "Домен: $DOMAIN"
    
    info "Проверка DNS резолюции:"
    nslookup $DOMAIN || warning "DNS резолюция не работает"
    dig $DOMAIN A +short || warning "dig команда недоступна"
    
    info "Проверка портов:"
    echo "Порт 8000 (приложение):"
    netstat -tlnp | grep :8000 || ss -tlnp | grep :8000 || warning "Порт 8000 не слушается"
    
    echo "Порт 80 (HTTP):"
    netstat -tlnp | grep :80 || ss -tlnp | grep :80 || warning "Порт 80 не используется"
    
    echo "Порт 443 (HTTPS):"
    netstat -tlnp | grep :443 || ss -tlnp | grep :443 || warning "Порт 443 не используется"
    
    info "Проверка файрвола (UFW):"
    if command -v ufw &> /dev/null; then
        ufw status
    else
        warning "UFW не установлен"
    fi
    
    info "Проверка iptables:"
    iptables -L INPUT -n | grep -E "(8000|80|443)" || warning "Нет специальных правил для веб-портов"
    
    info "Тест подключения к приложению:"
    echo "1. Локальный тест:"
    curl -I http://localhost:8000/ 2>/dev/null && success "Localhost работает" || error "Localhost не работает"
    
    echo "2. Тест по IP:"
    curl -I http://$SERVER_IP:8000/ 2>/dev/null && success "IP подключение работает" || error "IP подключение не работает"
    
    echo "3. Тест по домену (если DNS работает):"
    if nslookup $DOMAIN > /dev/null 2>&1; then
        curl -I http://$DOMAIN:8000/ 2>/dev/null && success "Домен работает" || error "Домен не работает"
    else
        warning "Пропускаем тест домена (DNS не работает)"
    fi
    
    info "Проверка ALLOWED_HOSTS в приложении:"
    if [ -f .env ]; then
        echo "ALLOWED_HOSTS из .env:"
        grep ALLOWED_HOSTS .env || warning "ALLOWED_HOSTS не найден в .env"
    else
        warning "Файл .env не найден"
    fi
    
    info "Проверка контейнера:"
    docker-compose -f docker-compose.prod.yml ps web
    
    info "Проверка логов nginx (если используется):"
    docker logs fsp_nginx --tail=10 2>/dev/null || warning "Nginx контейнер не запущен"
    
    success "Диагностика завершена!"
    
    info "Рекомендации:"
    echo "1. Если localhost работает, но IP/домен нет - проблема с файрволом"
    echo "2. Если DNS не работает - обновите настройки домена"
    echo "3. Если порт 8000 не слушается - проблема с контейнером"
    echo "4. Проверьте ALLOWED_HOSTS в .env файле"
}

# Настройка и диагностика Nginx
setup_nginx() {
    info "🔧 Настройка и диагностика Nginx..."
    
    # Проверка статуса nginx контейнера
    info "Проверка статуса nginx контейнера:"
    docker-compose -f docker-compose.prod.yml ps nginx
    
    info "Логи nginx контейнера:"
    docker logs fsp_nginx --tail=20 2>/dev/null || warning "Nginx контейнер не найден или не запущен"
    
    info "Проверка конфигурации nginx:"
    if [ -f "nginx.conf" ]; then
        success "Файл nginx.conf найден"
        echo "Проверка синтаксиса конфигурации:"
        docker run --rm -v "$(pwd)/nginx.conf:/etc/nginx/nginx.conf:ro" nginx:alpine nginx -t 2>/dev/null && success "Конфигурация корректна" || error "Ошибка в конфигурации"
    else
        error "Файл nginx.conf не найден!"
    fi
    
    info "Проверка портов:"
    echo "Порт 80 (HTTP):"
    netstat -tlnp | grep :80 || ss -tlnp | grep :80 || warning "Порт 80 не слушается"
    
    echo "Порт 443 (HTTPS):"
    netstat -tlnp | grep :443 || ss -tlnp | grep :443 || warning "Порт 443 не используется (SSL не настроен)"
    
    echo "Порт 8000 (Django):"
    netstat -tlnp | grep :8000 || ss -tlnp | grep :8000 || warning "Порт 8000 не слушается"
    
    info "Перезапуск nginx (если нужно):"
    read -p "Перезапустить nginx контейнер? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        info "Остановка nginx..."
        docker-compose -f docker-compose.prod.yml stop nginx
        
        info "Удаление старого контейнера..."
        docker-compose -f docker-compose.prod.yml rm -f nginx
        
        info "Запуск nginx..."
        docker-compose -f docker-compose.prod.yml up -d nginx
        
        info "Ожидание запуска (10 секунд)..."
        sleep 10
        
        info "Новый статус nginx:"
        docker-compose -f docker-compose.prod.yml ps nginx
    fi
    
    info "Тестирование подключений:"
    SERVER_IP=$(hostname -I | awk '{print $1}')
    
    echo "Тест прямого подключения к Django (порт 8000):"
    curl -I http://localhost:8000/ 2>/dev/null && success "Django доступен напрямую" || error "Django недоступен"
    
    echo "Тест через nginx (порт 80):"
    curl -I http://localhost/ 2>/dev/null && success "Nginx проксирует запросы" || error "Nginx не работает"
    
    echo "Тест по внешнему IP через nginx:"
    curl -I http://$SERVER_IP/ 2>/dev/null && success "Внешний доступ через nginx работает" || error "Внешний доступ не работает"
    
    info "Проверка файрвола:"
    if command -v ufw &> /dev/null; then
        echo "Статус UFW:"
        ufw status
        
        echo "Открытие необходимых портов:"
        ufw allow 80/tcp
        ufw allow 443/tcp
        ufw allow 8000/tcp
        ufw --force enable
        success "Порты 80, 443, 8000 открыты"
    else
        warning "UFW не установлен"
    fi
    
    success "Диагностика nginx завершена!"
    
    info "Рекомендации:"
    echo "1. Если nginx не запущен - перезапустите его выше"
    echo "2. Если порт 80 не слушается - проверьте конфликты с другими сервисами"
    echo "3. Для доступа по домену используйте порт 80 (nginx) вместо 8000"
    echo "4. Убедитесь, что DNS домена указывает на IP: $SERVER_IP"
}

# Обновление образов
update() {
    info "Обновление Docker образов..."
    docker pull ghcr.io/grigra27/fair_sber_price-web:latest || warning "Не удалось обновить web образ"
    docker pull ghcr.io/grigra27/fair_sber_price-bot:latest || warning "Не удалось обновить bot образ"
    docker pull redis:7-alpine
    docker pull nginx:alpine
    
    info "Перезапуск с новыми образами..."
    docker-compose -f docker-compose.prod.yml up -d
    
    success "Образы обновлены"
}

# Резервная копия
backup() {
    local backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    info "Создание резервной копии..."
    
    # Копирование базы данных
    cp fsp/db.sqlite3 "$backup_dir/" 2>/dev/null || warning "Не удалось скопировать базу данных"
    
    # Копирование логов
    cp -r fsp/logs "$backup_dir/" 2>/dev/null || warning "Не удалось скопировать логи"
    
    # Копирование конфигурации
    cp .env "$backup_dir/" 2>/dev/null || warning "Не удалось скопировать .env"
    cp docker-compose.prod.yml "$backup_dir/"
    
    success "Резервная копия создана: $backup_dir"
}

# Очистка
clean() {
    info "Очистка неиспользуемых ресурсов..."
    docker system prune -f
    docker volume prune -f
    success "Очистка завершена"
}

# Основная логика
main() {
    check_project_dir
    
    case "${1:-help}" in
        deploy)     deploy ;;
        start)      start ;;
        stop)       stop ;;
        restart)    restart ;;
        status)     status ;;
        logs)       logs "$2" ;;
        health)     health ;;
        fix)        fix ;;
        fix-bot)    fix_bot ;;
        fix-perms)  fix_permissions ;;
        debug-404)  debug_404 ;;
        debug-bot)  debug_bot ;;
        debug-net)  debug_network ;;
        nginx)      setup_nginx ;;
        update)     update ;;
        backup)     backup ;;
        clean)      clean ;;
        help|--help|-h) show_help ;;
        *)          error "Неизвестная команда: $1"; show_help; exit 1 ;;
    esac
}

main "$@"