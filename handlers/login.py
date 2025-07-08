import time
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from utils.storage import load_json, save_json
from utils.auth import login
from handlers.courses import send_course_selection_keyboard
from config import USER_DATA_FILE
from keyboards.reply import main_menu_keyboard

router = Router()


@router.message(Command("login"))
async def cmd_login(message: Message):
    parts = message.text.split(maxsplit=2)
    if len(parts) != 3:
        return await message.answer(
            "⚠️ Неверный формат. Используйте:\n"
            "<code>/login ваш_логин ваш_пароль</code>",
            parse_mode="HTML"
        )

    _, username, password = parts
    session = await login(username, password)
    if not session:
        return await message.answer(
            "❌ Ошибка авторизации. Проверьте логин и пароль!\n"
            "Попробуйте снова: <code>/login ваш_логин ваш_пароль</code>",
            parse_mode="HTML"
        )

    await session.close()

    users = load_json(USER_DATA_FILE, {})
    uid = str(message.chat.id)

    # Сохраняем данные пользователя
    users[uid] = {
        "username": username,
        "password": password,
        "subscriptions": [],
        "state": "choosing_courses",
        "last_update": int(time.time())
    }
    save_json(USER_DATA_FILE, users)

    await message.answer(
        "✅ Авторизация прошла успешно!\n"
        "Теперь выберите курсы для отслеживания:",
        reply_markup=main_menu_keyboard()
    )
    await send_course_selection_keyboard(message)