from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🔍 Проверить объявления"),
                KeyboardButton(text="📝  Найти конспект")
            ],
            [
                KeyboardButton(text="📅 Узнать расписание"),
                KeyboardButton(text="⚙️ Настройки")
            ]
        ],
        resize_keyboard=True
    )

def settings_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📚 Изменить курсы"),
                KeyboardButton(text="👨‍💻 Контакты разработчиков")
            ],
            [
                KeyboardButton(text="💙 Поддержать проект"),
                KeyboardButton(text="❌ Завершить работу")
            ],
            [
                KeyboardButton(text="🔙 Назад")
            ]
        ],
        resize_keyboard=True
    )

# Добавляем недостающую функцию
def login_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚀 Начать работу")]
        ],
        resize_keyboard=True
    )

def period_keyboard():
    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text="Сегодня")],
            [KeyboardButton(text="Неделя")],
            [KeyboardButton(text="Месяц")],
            [KeyboardButton(text="Все")]
        ]
    )
    return keyboard