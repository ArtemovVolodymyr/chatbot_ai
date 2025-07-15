# === handlers/login.py ===

# Імпортуємо необхідні класи для Telegram-бота
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from db import get_user_by_email_password  # Функція для перевірки облікових даних у базі
from menu import show_main_menu  # Функція для показу головного меню після входу
import logging  # Для логування подій та помилок

# Налаштування логера
logger = logging.getLogger(__name__)

# Стан розмови (етапи логіну)
LOGIN_EMAIL, LOGIN_PASSWORD = range(2)

# === ПЕРШИЙ КРОК ===
# Функція, яка запускає процес авторизації — запитує email
async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введіть ваш email:")
    return LOGIN_EMAIL  # Переходимо до наступного етапу (введення email)

# === ДРУГИЙ КРОК ===
# Отримуємо email, зберігаємо в user_data і запитуємо пароль
async def get_login_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["email"] = update.message.text  # Зберігаємо email у контексті користувача
    await update.message.reply_text("Введіть пароль:")
    return LOGIN_PASSWORD  # Переходимо до етапу перевірки пароля

# === ТРЕТІЙ КРОК ===
# Перевіряємо правильність введених email і пароля
async def check_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = context.user_data.get("email")  # Отримуємо email із контексту
    password = update.message.text  # Отримуємо введений пароль

    try:
        # Перевіряємо облікові дані в базі даних
        user = get_user_by_email_password(email, password)
        if user:
            # Якщо користувача знайдено — вітаємо та показуємо головне меню
            await update.message.reply_text(f"Вітаємо, {user['full_name']}!")
            await show_main_menu(update, context)
        else:
            # Якщо облікові дані невірні — повідомляємо про це
            await update.message.reply_text("Невірний email або пароль.")
    except Exception:
        # У разі помилки логування винятку та повідомлення користувачу
        logger.exception("Помилка під час входу:")
        await update.message.reply_text("Виникла помилка при перевірці входу.")

    # Завершуємо розмову, незалежно від результату
    return ConversationHandler.END
