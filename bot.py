# Імпортуємо необхідні бібліотеки та модулі
import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, ConversationHandler, filters
)
from dotenv import load_dotenv

# Імпортуємо функції з локальних модулів
from db import (
    get_connection, init_db, add_feedback, get_feedback,
    save_course_to_db, get_saved_courses
)
from cisco_api import get_courses, format_courses
from handlers.register import register, get_name, get_email, get_password, NAME, EMAIL, PASSWORD
from handlers.login import login, get_login_email, check_login, LOGIN_EMAIL, LOGIN_PASSWORD
from handlers.guest import guest

# Завантаження змінних середовища
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Константи для станів у ConversationHandler
ASK_INTEREST, ASK_LEVEL, FEEDBACK = range(3)
SAVE_COURSE_SELECTION = range(3, 4)[0]
ADMIN_ID = 397447568  # ID адміністратора для перевірки прав

# Головне меню
main_menu_keyboard = ReplyKeyboardMarkup(
    [["📚 Рекомендації", "✉️ Зворотній зв'язок"],
     ["👤 Користувачі", "📥 Відгуки"],
     ["💝 Зберегти курс", "📂 Мої курси"],
     ["🔄 На головну"]],
    resize_keyboard=True
)

# Початкове меню
start_keyboard = ReplyKeyboardMarkup(
    [["Реєстрація", "Увійти", "Увійти як гість"]],
    resize_keyboard=True,
    one_time_keyboard=True
)

# Обробник команди /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Вітаємо! Оберіть опцію для продовження:",
        reply_markup=start_keyboard
    )

# Повертає список доступних тем
def get_unique_topics():
    return ["Безпека", "Мережі", "Програмування", "DevNet", "Автоматизація", "Python"]

# Запит інтересів користувача
async def recommend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topics = get_unique_topics()
    keyboard = [topics[i:i + 3] for i in range(0, len(topics), 3)]
    keyboard.append(['🔙 Назад', '🔄 На головну'])
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        "Які теми вас цікавлять? Виберіть з кнопок або введіть свою тему:",
        reply_markup=reply_markup
    )
    return ASK_INTEREST

# Запит рівня знань користувача
async def ask_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text in ['🔙 Назад', '🔄 На головну']:
        await show_main_menu(update, context)
        return ConversationHandler.END

    context.user_data["interest"] = text
    level_keyboard = ReplyKeyboardMarkup(
        [["Початковий", "Середній", "Просунутий"],
         ["🔙 Назад", "🔄 На головну"]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await update.message.reply_text(
        "Який у вас рівень підготовки? Оберіть зі списку:",
        reply_markup=level_keyboard
    )
    return ASK_LEVEL

# Показує рекомендовані курси
async def show_courses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text in ["🔙 Назад", "🔄 На головну"]:
        await show_main_menu(update, context)
        return ConversationHandler.END

    level = text
    interest = context.user_data.get("interest", "")
    user_id = update.effective_user.id
    username = update.effective_user.username or ""

    # Збереження інтересу та рівня користувача в базу
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO users (telegram_id, username, interest, level)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (telegram_id)
                    DO UPDATE SET interest = EXCLUDED.interest, level = EXCLUDED.level;
                """, (user_id, username, interest, level))
                conn.commit()
    except Exception:
        logger.exception("Помилка при оновленні інформації користувача")

    # Отримання курсів та збереження їх у контексті
    courses = get_courses(interest=interest, level=level)
    context.user_data['last_courses'] = courses

    if courses:
        msg = format_courses(courses, interest=interest, level=level)
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=main_menu_keyboard)
    else:
        await update.message.reply_text(
            "🔍 На жаль, не знайдено курсів у базі Cisco.\n🔎 Спробуємо знайти схожі курси...",
            reply_markup=main_menu_keyboard
        )
        await update.message.reply_text(
            "⚠️ AI-рекомендації тимчасово недоступні. Спробуйте пізніше або змініть тему.",
            reply_markup=main_menu_keyboard
        )

    return ConversationHandler.END

# Запит на вибір курсу для збереження
async def save_course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    courses = context.user_data.get("last_courses")
    if not courses:
        await update.message.reply_text("❌ Спочатку отримайте рекомендації курсів, щоб їх зберегти.", reply_markup=main_menu_keyboard)
        return ConversationHandler.END

    keyboard = [[course['title']] for course in courses]
    keyboard.append(['🔙 Назад'])
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        "Оберіть курс, який хочете зберегти:",
        reply_markup=reply_markup
    )
    return SAVE_COURSE_SELECTION

# Збереження вибраного курсу
async def save_course_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    selected_title = update.message.text
    if selected_title == '🔙 Назад':
        await update.message.reply_text("Операцію скасовано.", reply_markup=main_menu_keyboard)
        return ConversationHandler.END

    courses = context.user_data.get('last_courses', [])
    course_to_save = next((c for c in courses if c['title'] == selected_title), None)

    if not course_to_save:
        await update.message.reply_text("Курс не знайдено, спробуйте ще раз.", reply_markup=main_menu_keyboard)
        return ConversationHandler.END

    success = save_course_to_db(user_id, course_to_save)
    if success:
        await update.message.reply_text(f"✅ Курс '{selected_title}' успішно збережено.", reply_markup=main_menu_keyboard)
    else:
        await update.message.reply_text(f"❌ Помилка збереження курсу '{selected_title}'.", reply_markup=main_menu_keyboard)

    return ConversationHandler.END

# Перегляд збережених курсів
async def view_saved_courses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    saved = get_saved_courses(user_id)
    if not saved:
        await update.message.reply_text("У вас немає збережених курсів.", reply_markup=main_menu_keyboard)
        return

    msg = "💾 Ваші збережені курси:\n\n"
    for c in saved:
        created_at = c['created_at'].strftime('%Y-%m-%d') if c['created_at'] else '—'
        msg += (
            f"📘 {c['course_title']}\n"
            f"📝 {c['course_description']}\n"
            f"Дата збереження: {created_at}\n\n"
        )
    await update.message.reply_text(msg.strip(), reply_markup=main_menu_keyboard)

# Показує головне меню
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Головне меню:",
        reply_markup=main_menu_keyboard
    )

# Скасування операції
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операція скасована.", reply_markup=main_menu_keyboard)
    return ConversationHandler.END

# Перегляд усіх користувачів (тільки для адміністратора)
async def get_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Вибачте, у вас немає прав для перегляду користувачів.", reply_markup=main_menu_keyboard)
        return

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT telegram_id, username, full_name, email FROM users ORDER BY telegram_id;")
                users = cur.fetchall()
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        users = []

    if not users:
        await update.message.reply_text("Список користувачів порожній.", reply_markup=main_menu_keyboard)
        return

    msg = "👥 Зареєстровані користувачі:\n\n"
    for u in users:
        msg += (
            f"ID: {u['telegram_id']}\n"
            f"Ім'я: {u.get('full_name', '—')}\n"
            f"Нікнейм: @{u.get('username', '—')}\n"
            f"Email: {u.get('email', '—')}\n\n"
        )
    await update.message.reply_text(msg.strip(), reply_markup=main_menu_keyboard)

# Ввід тексту відгуку
async def feedback_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Введіть ваш відгук або /cancel для скасування:",
        reply_markup=ReplyKeyboardMarkup([["/cancel"]], resize_keyboard=True, one_time_keyboard=True)
    )
    return FEEDBACK

# Збереження відгуку
async def feedback_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "/cancel":
        await update.message.reply_text("Операцію скасовано.", reply_markup=main_menu_keyboard)
        return ConversationHandler.END

    user_id = update.effective_user.id
    try:
        add_feedback(user_id, text)
    except Exception as e:
        logger.error(f"Error adding feedback: {e}")
        await update.message.reply_text("❌ Сталася помилка при додаванні відгуку.", reply_markup=main_menu_keyboard)
        return ConversationHandler.END

    await update.message.reply_text("Дякуємо за ваш відгук!", reply_markup=main_menu_keyboard)
    return ConversationHandler.END

# Перегляд усіх відгуків
async def view_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    try:
        feedbacks = get_feedback()
    except Exception as e:
        logger.error(f"Error getting feedbacks: {e}")
        feedbacks = []

    if not feedbacks:
        await update.message.reply_text("Відгуків ще немає.", reply_markup=main_menu_keyboard)
        return

    msg = "📢 Відгуки:\n\n"
    for fb in feedbacks:
        if user_id == ADMIN_ID:
            try:
                with get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT username, full_name FROM users WHERE telegram_id = %s;", (fb['user_id'],))
                        user = cur.fetchone()
                author = user['full_name'] or user['username'] if user else "Не відомо"
            except Exception as e:
                logger.error(f"Error fetching author info: {e}")
                author = "Не відомо"
            msg += f"Від: {author}\n"
        else:
            msg += "Відгук:\n"
        msg += f"{fb['message']}\n\n"

    await update.message.reply_text(msg.strip(), reply_markup=main_menu_keyboard)

# Головна функція запуску бота
def main():
    init_db()  # Ініціалізація бази даних

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Реєстрація обробників
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^🔄 На головну$"), show_main_menu))

    # Реєстрація
    register_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Реєстрація$"), register)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_password)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(register_handler)

    # Вхід
    login_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Увійти$"), login)],
        states={
            LOGIN_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_login_email)],
            LOGIN_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_login)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(login_handler)

    # Гостьовий вхід
    app.add_handler(MessageHandler(filters.Regex("^Увійти як гість$"), guest))

    # Рекомендації курсів
    recommend_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📚 Рекомендації$"), recommend)],
        states={
            ASK_INTEREST: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_level)],
            ASK_LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, show_courses)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(recommend_handler)

    # Збереження курсів
    save_course_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^💝 Зберегти курс$"), save_course)],
        states={
            SAVE_COURSE_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_course_selection)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(save_course_handler)

    # Інші дії
    app.add_handler(MessageHandler(filters.Regex("^📂 Мої курси$"), view_saved_courses))
    app.add_handler(MessageHandler(filters.Regex("^👤 Користувачі$"), get_users))

    feedback_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^✉️ Зворотній зв'язок$"), feedback_entry)],
        states={
            FEEDBACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, feedback_save)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(feedback_handler)

    app.add_handler(MessageHandler(filters.Regex("^📥 Відгуки$"), view_feedback))

    # Запуск бота
    app.run_polling()

# Точка входу
if __name__ == "__main__":
    main()
