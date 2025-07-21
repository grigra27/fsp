import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from asgiref.sync import sync_to_async
from price.services import sber_service

logger = logging.getLogger('telegrambot')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    welcome_msg = (
        "🏦 Добро пожаловать в бот справедливой оценки акций Сбербанка!\n\n"
        "Доступные команды:\n"
        "/info - получить текущие данные\n"
        "/history - краткая история цен\n"
        "/help - показать эту справку"
    )
    await update.message.reply_text(welcome_msg)
    await send_current_info(update, context)


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /info command"""
    await send_current_info(update, context)


async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /history command"""
    try:
        # Use sync_to_async to call Django ORM methods
        get_historical_data = sync_to_async(sber_service.get_historical_data)
        snapshots = await get_historical_data(days=7)
        
        # Convert QuerySet to list to avoid async issues
        snapshots_list = await sync_to_async(list)(snapshots)
        
        if not snapshots_list:
            await update.message.reply_text("📊 Исторические данные пока недоступны")
            return
        
        msg = "📈 История за последние 7 дней:\n\n"
        for snapshot in snapshots_list[:5]:  # Show last 5 entries
            date_str = snapshot.timestamp.strftime('%d.%m %H:%M')
            msg += (
                f"📅 {date_str}\n"
                f"💰 MOEX: {snapshot.moex_price or 'Н/Д'} ₽\n"
                f"⚖️ Справедливая: {snapshot.fair_price or 'Н/Д'} ₽\n"
                f"📊 P/B: {snapshot.pb_ratio or 'Н/Д'}\n"
                f"🎯 Оценка: {snapshot.price_score}\n\n"
            )
        
        await update.message.reply_text(msg)
        
    except Exception as e:
        logger.error(f"Error in history command: {e}")
        await update.message.reply_text("❌ Ошибка при получении исторических данных")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_msg = (
        "🤖 Справка по боту:\n\n"
        "📊 /info - текущие данные по акции\n"
        "📈 /history - история за последние дни\n"
        "❓ /help - эта справка\n\n"
        "🔄 Данные обновляются автоматически с кешированием\n"
        "⏰ Кеш: 1 минута в торговые часы, 5 минут в остальное время\n\n"
        "📝 Оценки:\n"
        "🟢 дешево - P/B < 1.0\n"
        "🔵 справедливо - P/B 1.0-1.2\n"
        "🟡 чуть дорого - P/B 1.2-1.4\n"
        "🔴 дорого - P/B > 1.4"
    )
    await update.message.reply_text(help_msg)


async def send_current_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send current price information"""
    try:
        # Send "typing" action
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # Use sync_to_async to call Django service methods
        get_current_data = sync_to_async(sber_service.get_current_data)
        data = await get_current_data()
        
        # Check if we have valid data
        if data['moex_price'] is None or data['fair_price'] is None:
            await update.message.reply_text(
                "⚠️ Не удалось получить актуальные данные.\n"
                "Возможно, биржа закрыта или есть проблемы с API."
            )
            return
        
        # Format price score with emoji
        score_emoji = {
            'дешево': '🟢',
            'справедливо': '🔵', 
            'чуть дорого': '🟡',
            'дорого': '🔴'
        }
        
        emoji = score_emoji.get(data['price_score'], '⚪')
        
        msg = (
            f"📊 Данные по акции Сбербанка:\n\n"
            f"💰 MOEX цена: {data['moex_price']} ₽\n"
            f"⚖️ Справедливая цена: {data['fair_price']} ₽\n"
            f"📈 Справедливая +20%: {data['fair_price_20_percent']} ₽\n"
            f"📊 P/B коэффициент: {data['pb_ratio']}\n"
            f"{emoji} Оценка: {data['price_score']}\n\n"
            f"🕐 Обновлено: {data['timestamp'].strftime('%d.%m.%Y %H:%M')}"
        )
        
        await update.message.reply_text(msg)
        logger.info(f"Sent price info to user {update.effective_user.id}")
        
    except Exception as e:
        logger.error(f"Error sending current info: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при получении данных.\n"
            "Попробуйте позже или обратитесь к администратору."
        )


async def handle_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unknown commands"""
    await update.message.reply_text(
        "❓ Неизвестная команда.\n"
        "Используйте /help для просмотра доступных команд."
    )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.message:
        await update.message.reply_text(
            "❌ Произошла техническая ошибка.\n"
            "Администратор уведомлен о проблеме."
        )


def run_bot():
    """Run the Telegram bot"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is not set!")
    
    # Create application
    app = ApplicationBuilder().token(token).build()
    
    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("info", info))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(CommandHandler("help", help_command))
    
    # Handle unknown commands
    app.add_handler(MessageHandler(filters.COMMAND, handle_unknown))
    
    # Add error handler
    app.add_error_handler(error_handler)
    
    logger.info("Starting Telegram bot...")
    
    # Run the bot
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )
