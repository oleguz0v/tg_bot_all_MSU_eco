from aiogram import Router
from aiogram.types import Message
from keyboards.reply import main_menu_keyboard, settings_menu_keyboard

router = Router()

@router.message(lambda m: m.text == "⚙️ Настройки")
async def show_settings(message: Message):
    # Убираем HTML-разметку для простоты
    await message.answer(
        "⚙️ Настройки бота\n\n"
        "Выберите действие:",
        reply_markup=settings_menu_keyboard()
    )

@router.message(lambda m: m.text == "🔙 Назад")
async def back_to_main_menu(message: Message):
    # Упрощаем сообщение
    await message.answer(
        "Главное меню:",
        reply_markup=main_menu_keyboard()
    )