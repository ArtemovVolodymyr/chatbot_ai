# === handlers/register.py ===

# Імпорт необхідних бібліотек
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from db import save_user  # Функція збереження користувача в базу даних
import logging
from menu import show_main_menu  # Меню, яке з’явиться після реєстрації

# Налаштування логування
logger = logging.getLogger(__name__)

# Кроки реєстрації у ConversationHandler
NAME, EMAIL, PASSWORD = range(3)

# === КРОК 1 ===
# Початок реєстрації — запит ПІБ
async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введіть ваше ПІБ:")
    return NAME  # Переходимо до наступного кроку — введення ПІБ

# === КРОК 2 ===
# Зберігаємо ПІБ користувача і запитуємо email
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text  # Зберігаємо повне ім’я в user_data
    await update.message.reply_text("Введіть ваш email:")
    return EMAIL  # Переходимо до введення email

# === КРОК 3 ===
# Зберігаємо email і запитуємо пароль
async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["email"] = update.message.text  # Зберігаємо email у контексті
    await update.message.reply_text("Придумайте пароль:")
    return PASSWORD  # Переходимо до введення пароля

# === КРОК 4 ===
# Завершальний етап: збереження користувача до бази
async def get_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id  # Telegram ID користувача
    username = update.effective_user.username or None  # Username або None, якщо відсутній
    full_name = context.user_data.get("name")  # ПІБ з попередніх кроків
    email = context.user_data.get("email")
    password = update.message.text  # Введений пароль

    try:
        # Спроба зберегти користувача в базу даних
        result = save_user(telegram_id, username, full_name, email, password)
        if result:
            # Успішна реєстрація — показуємо головне меню
            await update.message.reply_text("Реєстрація успішна!")
            await show_main_menu(update, context)
        else:
            # Якщо такий telegram_id уже існує в БД
            await update.message.reply_text("Користувач із таким telegram_id уже існує.")
    except Exception:
        # Логування винятку і повідомлення про помилку
        logger.exception("Помилка у процесі реєстрації:")
        await update.message.reply_text("Сталася непередбачена помилка при реєстрації.")

    return ConversationHandler.END  # Завершення діалогу реєстрації
