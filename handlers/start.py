from aiogram import Router
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import Command
from keyboards.reply import login_keyboard  # Исправленный импорт

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 Добро пожаловать в объединённого бота МГУ!\n\n"
        "Для начала работы необходимо авторизоваться.\n"
        "Нажмите кнопку '🚀 Начать работу' для входа.",
        reply_markup=login_keyboard()  # Используем правильную функцию
    )

@router.message(lambda m: m.text == "🚀 Начать работу")
async def begin(message: Message):
    await message.answer(
        "🔑 Для авторизации в боте и получении обновлений с Onecons введите команду:\n"
        "<code>/login ваш_логин ваш_пароль</code>\n\n"
        "Например: <code>/login student123 mypassword</code>",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )