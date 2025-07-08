from aiogram import Router
from aiogram.types import Message
from utils.storage import load_json, save_json
from config import USER_DATA_FILE
from keyboards.reply import login_keyboard

router = Router()


@router.message(lambda m: m.text == "❌ Завершить работу")
async def cmd_stop(message: Message):
    chat_id = str(message.chat.id)
    users = load_json(USER_DATA_FILE, {})

    if chat_id in users:
        users.pop(chat_id)
        save_json(USER_DATA_FILE, users)

    await message.answer(
        "🔒 Сессия завершена. Ваши данные удалены.\n"
        "Чтобы начать заново, нажмите «🚀 Начать работу».",
        reply_markup=login_keyboard()
    )