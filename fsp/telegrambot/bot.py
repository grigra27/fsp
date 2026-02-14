import os
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters
from asgiref.sync import sync_to_async
from price.services import sber_service

logger = logging.getLogger('telegrambot')


SCORE_EMOJI = {
    'дешево': '🟢',
    'справедливо': '🔵',
    'чуть дорого': '🟡',
    'дорого': '🔴',
}

METHOD_TEXT = (
    "🧠 Почему P/B = 1 считается справедливой оценкой?\n\n"
    "P/B (Price-to-Book) = 1 означает, что рыночная стоимость банка равна "
    "его балансовой стоимости (собственному капиталу).\n\n"
    "Для банков это базовый ориентир, потому что:\n"
    "• активы банков в основном финансовые и ближе к рыночной цене;\n"
    "• исторически P/B = 1 — часто встречаемый уровень для сектора;\n"
    "• при P/B < 1 акция может быть недооцененной."
)

RANGE_TEXT = (
    "📏 Почему диапазон P/B = 1.0–1.2?\n\n"
    "Этот диапазон считается зоной справедливой оценки для банков:\n"
    "• P/B = 1.0 — базовая справедливая стоимость;\n"
    "• P/B = 1.2 — премия за качество управления и перспективы роста;\n"
    "• выше 1.2 — акции становятся дорогими;\n"
    "• ниже 1.0 — потенциально недооцененные."
)

THESIS_TEXT = (
    "📌 Инвестиционный тезис\n\n"
    "Почему этот банк:\n"
    "• Лидер рынка: крупнейший банк России с долей ~30%;\n"
    "• Стабильность: государственная поддержка и системная значимость;\n"
    "• Дивиденды: высокая дивидендная доходность;\n"
    "• Цифровизация: инвестиции в IT и экосистему.\n\n"
    "Шкала оценки по P/B:\n"
    "🟢 Дешево: < 1.0\n"
    "🔵 Справедливо: 1.0–1.2\n"
    "🟡 Дорого: 1.2–1.4\n"
    "🔴 Очень дорого: > 1.4"
)

RISKS_TEXT = (
    "⚠️ Основные риски\n\n"
    "• Санкционные риски\n"
    "• Макроэкономическая нестабильность\n"
    "• Регулятивные изменения\n"
    "• Кредитные риски"
)


def get_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Текущая оценка", callback_data="current")],
        [InlineKeyboardButton("🧠 Почему P/B = 1", callback_data="method")],
        [InlineKeyboardButton("📏 Диапазон 1.0–1.2", callback_data="range")],
        [InlineKeyboardButton("📌 Инвесттезис", callback_data="thesis")],
        [InlineKeyboardButton("⚠️ Риски", callback_data="risks")],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    welcome_msg = (
        "🏦 Добро пожаловать в бот справедливой оценки акций Сбербанка!\n\n"
        "Доступные команды:\n"
        "/info - текущая оценка\n"
        "/thesis - инвестиционный тезис\n"
        "/method - почему P/B = 1\n"
        "/range - почему диапазон 1.0–1.2\n"
        "/risks - ключевые риски\n"
        "/help - справка"
    )
    await update.message.reply_text(welcome_msg, reply_markup=get_main_keyboard())
    await send_current_info(update, context)


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /info command"""
    await send_current_info(update, context)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_msg = (
        "🤖 Справка по боту:\n\n"
        "📊 /info - текущие данные по акции\n"
        "📌 /thesis - инвестиционный тезис\n"
        "🧠 /method - методология оценки P/B\n"
        "📏 /range - диапазон справедливой оценки\n"
        "⚠️ /risks - ключевые риски\n"
        "❓ /help - эта справка\n\n"
        "🔄 Данные обновляются автоматически с кешированием\n"
        "⏰ Кеш: 1 минута в торговые часы, 5 минут в остальное время\n\n"
        "📝 Оценки:\n"
        "🟢 дешево - P/B < 1.0\n"
        "🔵 справедливо - P/B 1.0-1.2\n"
        "🟡 чуть дорого - P/B 1.2-1.4\n"
        "🔴 дорого - P/B > 1.4"
    )
    await update.message.reply_text(help_msg, reply_markup=get_main_keyboard())


async def thesis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /thesis command"""
    await update.message.reply_text(THESIS_TEXT, reply_markup=get_main_keyboard())


async def method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /method command"""
    await update.message.reply_text(METHOD_TEXT, reply_markup=get_main_keyboard())


async def range_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /range command"""
    await update.message.reply_text(RANGE_TEXT, reply_markup=get_main_keyboard())


async def risks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /risks command"""
    await update.message.reply_text(RISKS_TEXT, reply_markup=get_main_keyboard())


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
        
        emoji = SCORE_EMOJI.get(data['price_score'], '⚪')
        
        msg = (
            f"📊 Данные по акции Сбербанка:\n\n"
            f"💰 MOEX цена: {data['moex_price']} ₽\n"
            f"⚖️ Справедливая цена: {data['fair_price']} ₽\n"
            f"📈 Справедливая +20%: {data['fair_price_20_percent']} ₽\n"
            f"📊 P/B коэффициент: {data['pb_ratio']}\n"
            f"{emoji} Оценка: {data['price_score']}\n\n"
            f"🕐 Обновлено: {data['timestamp'].strftime('%d.%m.%Y %H:%M')}"
        )
        
        await update.message.reply_text(msg, reply_markup=get_main_keyboard())
        logger.info(f"Sent price info to user {update.effective_user.id}")
        
    except Exception as e:
        logger.error(f"Error sending current info: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при получении данных.\n"
            "Попробуйте позже или обратитесь к администратору."
        )


async def handle_menu_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button actions."""
    query = update.callback_query
    await query.answer()

    if query.data == 'current':
        await send_current_info(update, context)
    elif query.data == 'method':
        await query.message.reply_text(METHOD_TEXT, reply_markup=get_main_keyboard())
    elif query.data == 'range':
        await query.message.reply_text(RANGE_TEXT, reply_markup=get_main_keyboard())
    elif query.data == 'thesis':
        await query.message.reply_text(THESIS_TEXT, reply_markup=get_main_keyboard())
    elif query.data == 'risks':
        await query.message.reply_text(RISKS_TEXT, reply_markup=get_main_keyboard())


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
        logger.error("TELEGRAM_BOT_TOKEN environment variable is not set!")
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is not set!")
    
    logger.info(f"Initializing bot with token: {token[:10]}...")
    
    try:
        # Create application
        app = ApplicationBuilder().token(token).build()
        
        # Add command handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("info", info))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("thesis", thesis))
        app.add_handler(CommandHandler("method", method))
        app.add_handler(CommandHandler("range", range_info))
        app.add_handler(CommandHandler("risks", risks))
        app.add_handler(CallbackQueryHandler(handle_menu_action))
        
        # Handle unknown commands
        app.add_handler(MessageHandler(filters.COMMAND, handle_unknown))
        
        # Add error handler
        app.add_error_handler(error_handler)
        
        logger.info("✅ Telegram bot handlers configured successfully")
        logger.info("🚀 Starting Telegram bot polling...")
        
        # Run the bot
        app.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            poll_interval=1.0,
            timeout=10
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        raise
