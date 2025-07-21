from django.core.management.base import BaseCommand
from telegrambot.bot import run_bot

class Command(BaseCommand):
    help = 'Запуск Telegram бота'

    def handle(self, *args, **options):
        run_bot()
