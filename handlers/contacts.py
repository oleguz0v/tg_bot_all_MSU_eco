from aiogram import Router
from aiogram.types import Message
from keyboards.reply import settings_menu_keyboard

router = Router()

@router.message(lambda m: m.text == "👨‍💻 Контакты разработчиков")
async def show_contacts(message: Message):
    await message.answer(
        "Социальный проект для студентов\n\n"
        "📅 Автоматическое отслеживание расписания\n"
        "🔍 Мгновенный поиск учебных материалов\n"
        "🤝 Поддержка студенческого сообщества\n\n"
        "Хотите создать подобный сервис для своего факультета?\nДелитесь идеями!\n"
        "Вместе построим удобную инфраструктуру для всех направлений.\n"
        "Знания становятся сильнее, когда ими делишься.\n\n"
        "📞 Контакты разработчиков:\n\n"
        "• Основной разработчик: @oleguzov\n"
        "• Группа обсуждений: t.me/pisulki_project\n",
        reply_markup=settings_menu_keyboard()
    )