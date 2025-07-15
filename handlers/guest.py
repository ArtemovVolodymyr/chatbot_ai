# === handlers/guest.py ===

# Імпортуємо класи для роботи з Telegram API
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from menu import show_main_menu  # Імпортуємо функцію для показу головного меню
import logging  # Для логування помилок

# Створення логера для запису інформації або помилок
logger = logging.getLogger(__name__)


# Асинхронна функція обробки "гість" (вхід без реєстрації)
async def guest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Повідомляємо користувачу, що він увійшов як гість
        await update.message.reply_text("Ви увійшли як гість.")

        # Виводимо головне меню (відповідно до ролі)
        await show_main_menu(update, context)

    except Exception:
        # Логування будь-якої помилки, що виникає під час виконання
        logger.exception("Помилка при вході як гість:")

        # Інформуємо користувача про помилку
        await update.message.reply_text("Виникла помилка при доступі у режимі гостя.")

    # Завершення поточної розмови (ConversationHandler)
    return ConversationHandler.END
