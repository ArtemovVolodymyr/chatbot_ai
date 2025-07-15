# === db.py ===

# Імпорт необхідних бібліотек
import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor  # Повертає результати у вигляді словника
from dotenv import load_dotenv  # Завантаження змінних середовища з .env

# Завантаження конфігурації з .env файлу
load_dotenv()
logger = logging.getLogger(__name__)

# Зчитування параметрів підключення до бази даних із .env
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

# Отримання з'єднання з базою даних
def get_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

# Ініціалізація бази даних: створення таблиць, якщо вони не існують
def init_db():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Таблиця користувачів
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        telegram_id BIGINT PRIMARY KEY,
                        username TEXT,
                        full_name TEXT,
                        email TEXT UNIQUE,
                        password TEXT,
                        role TEXT DEFAULT 'студент',  -- ролі: 'адмін', 'студент', 'гість'
                        interest TEXT,
                        level TEXT,
                        goals TEXT
                    );
                """)
                # Таблиця відгуків
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS feedback (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
                        message TEXT,
                        created_at TIMESTAMP DEFAULT NOW()
                    );
                """)
                # Таблиця збережених курсів
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS saved_courses (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
                        course_title TEXT,
                        course_description TEXT,
                        created_at TIMESTAMP DEFAULT NOW(),
                        UNIQUE(user_id, course_title)  -- запобігає дублюванню курсів
                    );
                """)
                # Індекс для швидкого пошуку користувача за email
                cur.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")
                conn.commit()
        logger.info("База даних ініціалізована успішно.")
    except Exception:
        logger.exception("Помилка при ініціалізації бази даних:")

# Збереження відгуку користувача
def add_feedback(user_id, message):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO feedback (user_id, message)
                    VALUES (%s, %s);
                """, (user_id, message))
                conn.commit()
    except Exception:
        logger.exception("Помилка при збереженні відгуку:")

# Отримання всіх відгуків або відгуків конкретного користувача
def get_feedback(user_id=None):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                if user_id:
                    cur.execute("SELECT * FROM feedback WHERE user_id = %s ORDER BY created_at DESC;", (user_id,))
                else:
                    cur.execute("SELECT * FROM feedback ORDER BY created_at DESC;")
                return cur.fetchall()
    except Exception:
        logger.exception("Помилка при отриманні відгуків:")
        return []

# Збереження користувача (уникнення дублювання по telegram_id)
def save_user(telegram_id, username, full_name, email, password, role='студент'):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO users (telegram_id, username, full_name, email, password, role)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (telegram_id) DO NOTHING;
                """, (telegram_id, username, full_name, email, password, role))
                conn.commit()
        return True
    except Exception:
        logger.exception("Помилка при збереженні користувача:")
        return False

# Отримання користувача за email та паролем (вхід)
def get_user_by_email_password(email, password):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
                return cur.fetchone()
    except Exception:
        logger.exception("Помилка при вході користувача:")
        return None

# Отримання користувача за Telegram ID
def get_user_by_id(telegram_id):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE telegram_id=%s", (telegram_id,))
                return cur.fetchone()
    except Exception:
        logger.exception("Помилка при отриманні користувача:")
        return None

# Отримання списку всіх зареєстрованих користувачів (тільки базова інформація)
def get_all_users():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT telegram_id, username, full_name, email, role FROM users ORDER BY telegram_id;")
                return cur.fetchall()
    except Exception:
        logger.exception("Помилка при отриманні користувачів:")
        return []

# Збереження курсу до обраного користувача
def save_course_to_db(user_id, course):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO saved_courses (user_id, course_title, course_description)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id, course_title) DO NOTHING;
                """, (user_id, course['title'], course['description']))
                conn.commit()
        return True
    except Exception:
        logger.exception("Помилка при збереженні курсу в БД:")
        return False

# Отримання збережених курсів користувача
def get_saved_courses(user_id):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT course_title, course_description, created_at
                    FROM saved_courses WHERE user_id = %s ORDER BY created_at DESC;
                """, (user_id,))
                return cur.fetchall()
    except Exception:
        logger.exception("Помилка при отриманні збережених курсів:")
        return []
