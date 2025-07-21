import os
import logging
from django.core.management.base import BaseCommand
from telegrambot.bot import run_bot

logger = logging.getLogger('telegrambot')

class Command(BaseCommand):
    help = 'Запуск Telegram бота'

    def handle(self, *args, **options):
        # Проверяем наличие токена
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            self.stdout.write(
                self.style.ERROR('❌ TELEGRAM_BOT_TOKEN не установлен!')
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS('🤖 Запуск Telegram бота...')
        )
        
        try:
            run_bot()
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('⏹️ Бот остановлен пользователем')
            )
        except Exception as e:
            logger.error(f"Критическая ошибка бота: {e}")
            self.stdout.write(
                self.style.ERROR(f'❌ Критическая ошибка: {e}')
            )
            raise
