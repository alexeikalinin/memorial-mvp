"""
Точка входа Telegram-бота.

Запуск:
    cd backend && source .venv/bin/activate && python -m bot.main
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from app.config import settings
from bot.handlers import (
    start,
    change,
    voice_toggle,
    family_toggle,
    help_cmd,
    message_handler,
    callback_handler,
)


def run() -> None:
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN не задан в .env — бот не запущен.")
        sys.exit(1)

    print("🤖 Запуск Telegram-бота...")
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("change", change))
    app.add_handler(CommandHandler("voice", voice_toggle))
    app.add_handler(CommandHandler("family", family_toggle))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print(f"✅ Бот запущен (polling). API: {settings.BOT_API_BASE_URL}")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    run()
