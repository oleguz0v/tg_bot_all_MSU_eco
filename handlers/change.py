from aiogram import Router
from aiogram.types import Message
from utils.storage import load_json, save_json
from handlers.courses import send_course_selection_keyboard
from config import USER_DATA_FILE
from keyboards.reply import main_menu_keyboard

router = Router()

@router.message(lambda m: m.text == "📚 Изменить курсы")
async def cmd_change_courses(message: Message):
    chat_id = str(message.chat.id)
    users = load_json(USER_DATA_FILE, {})
    if chat_id not in users:
        return await message.answer("⚠️ Сначала авторизуйтесь: /login", reply_markup=main_menu_keyboard())
    # Сбросьте состояние, если используете state-machine
    users[chat_id]["state"] = "choosing_courses"
    save_json(USER_DATA_FILE, users)
    # Показываем клавиатуру выбора курсов
    await send_course_selection_keyboard(message)