# === cisco_api.py ===

# Імпорт бібліотек
from dotenv import load_dotenv  # Для завантаження змінних середовища з .env
import logging  # Для ведення логів

# Завантаження змінних з .env (наразі не використовується, але залишено для сумісності)
load_dotenv()
logger = logging.getLogger(__name__)

# Базове посилання на Cisco, може бути використане для посилань у майбутньому
BASE_URL = "https://www.cisco.com/c/en/us/training-events/training-certifications/training/"

# Функція для отримання курсів за темою (interest) та рівнем складності (level)
def get_courses(interest=None, level=None):
    # Відображення локалізованих назв рівнів на англійські назви
    level_map = {
        "початковий": "Beginner",
        "середній": "Intermediate",
        "просунутий": "Advanced",
        "beginner": "Beginner",
        "intermediate": "Intermediate",
        "advanced": "Advanced"
    }

    # Якщо вказано рівень, перетворюємо його до потрібного формату
    if level:
        level = level_map.get(level.lower(), level.capitalize())

    logger.info(f"Шукаємо курси з темою '{interest}' та рівнем '{level}'")

    # Емуляція бази даних курсів (локальний список)
    courses_db = [
        {"title": "Python Essentials", "description": "Вступ до Python, змінні, цикли, умови, функції та об’єктне програмування.", "level": "Beginner", "duration": "8 hours", "free": True, "mode": "Self-paced"},
        {"title": "Introduction to Cybersecurity", "description": "Основи кібербезпеки, загрози, атаки, захист даних.", "level": "Beginner", "duration": "6 hours", "free": True, "mode": "Self-paced"},
        {"title": "CCNA: Introduction to Networks", "description": "Основи мереж, IP-адресація, маршрутизація, моделі OSI та TCP/IP.", "level": "Beginner", "duration": "40 hours", "free": True, "mode": "Self-paced"},
        {"title": "Cybersecurity Essentials", "description": "Поглиблений курс з безпеки мереж, загроз, криптографії.", "level": "Intermediate", "duration": "30 hours", "free": True, "mode": "Self-paced"},
        {"title": "DevNet Associate", "description": "Програмування мереж, API, автоматизація з Cisco DevNet.", "level": "Intermediate", "duration": "40 hours", "free": True, "mode": "Self-paced"},
        {"title": "Networking Essentials", "description": "Концепції мереж, TCP/IP, конфігурація маршрутизаторів та комутаторів.", "level": "Intermediate", "duration": "20 hours", "free": True, "mode": "Self-paced"},
        {"title": "CyberOps Associate", "description": "SOC-операції, виявлення загроз, реагування на інциденти.", "level": "Advanced", "duration": "60 hours", "free": False, "mode": "Instructor-led"},
        {"title": "Network Security", "description": "Захист мережі, брандмауери, VPN, політики безпеки.", "level": "Advanced", "duration": "50 hours", "free": False, "mode": "Instructor-led"},
        {"title": "DevNet Automation", "description": "Автоматизація конфігурацій мереж за допомогою Python і REST API.", "level": "Advanced", "duration": "45 hours", "free": False, "mode": "Self-paced"},
        {"title": "IoT Fundamentals", "description": "Основи Інтернету речей, підключення пристроїв, безпека IoT.", "level": "Beginner", "duration": "10 hours", "free": True, "mode": "Self-paced"}
    ]

    # Фільтрація курсів відповідно до вказаного інтересу та рівня
    filtered = []
    interest_lower = interest.lower() if interest else None  # Приведення інтересу до нижнього регістру
    for course in courses_db:
        # Якщо вказано інтерес і він не входить у назву або опис — пропустити курс
        if interest_lower and interest_lower not in course["title"].lower() and interest_lower not in course["description"].lower():
            continue
        # Якщо вказано рівень і він не відповідає — пропустити
        if level and course["level"] != level:
            continue
        # Якщо курс відповідає фільтрам — додати до результату
        filtered.append(course)

    logger.info(f"Знайдено курсів: {len(filtered)}")
    return filtered

# Функція форматування списку курсів у текстовий вигляд для відправки користувачу
def format_courses(courses, interest=None, level=None):
    if not courses:
        # Якщо немає результатів — повідомити користувача
        return f"🔍 На жаль, не знайдено курсів за темою «{interest}» та рівнем «{level}»."

    # Формування заголовку повідомлення
    result = f"🔍 Ось курси за темою «{interest}», рівень: «{level}»:\n"

    # Додавання опису кожного курсу до результату
    for course in courses:
        result += (
            f"\n📘 {course['title']}\n"
            f"📝 {course['description']}\n"
            f"📊 {course['level']}\n"
            f"⏱️ {course['duration']}\n"
            f"💰 {'Безкоштовний' if course['free'] else 'Платний'} | 🧑‍🏫 {course['mode']}\n"
        )
    return result.strip()
