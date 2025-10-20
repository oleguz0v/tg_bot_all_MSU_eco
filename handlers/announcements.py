import time
import logging
from aiogram import Router
from aiogram.types import Message
from utils.storage import load_json, save_json
from utils.auth import login
from utils.parser import get_announcements
from utils.hashing import get_course_hash, get_course_hash_v1, matches_existing_hash
from utils.locks import get_lock
from config import USER_DATA_FILE, ANNOUNCEMENTS_FILE
from keyboards.reply import main_menu_keyboard, login_keyboard

router = Router()


async def check_and_notify(chat_id: int, bot):
    users = load_json(USER_DATA_FILE, {})
    user = users.get(str(chat_id))

    # Проверка авторизации
    if not user or not user.get("subscriptions"):
        await bot.send_message(
            chat_id,
            "⚠️ Вы не подписаны ни на один курс. "
            "Используйте «📚 Изменить курсы» в настройках.",
            reply_markup=main_menu_keyboard()
        )
        return

    session = await login(user["username"], user["password"])
    if not session:
        logging.error(f"Auth failed for user {chat_id}")
        await bot.send_message(
            chat_id,
            "❌ Ошибка авторизации. Проверьте логин и пароль!",
            reply_markup=main_menu_keyboard()
        )
        return

    any_new = False
    ann = load_json(ANNOUNCEMENTS_FILE, {})

    for course_name in user["subscriptions"]:
        url = user["available_courses"].get(course_name)
        if not url:
            continue

        # Получаем объявления
        anns = await get_announcements(session, url)
        if not anns:
            continue
        new_hash = get_course_hash(anns)

        # Вся логика проверки и обновления под одним URL-локом
        url_lock = get_lock(f"url:{url}")
        async with url_lock:
            fresh_ann = load_json(ANNOUNCEMENTS_FILE, {})
            fresh_record = fresh_ann.get(url)
            
            # Первая инициализация без уведомлений
            if fresh_record is None:
                fresh_ann[url] = {"page_hash": new_hash, "last_found": int(time.time())}
                save_json(ANNOUNCEMENTS_FILE, fresh_ann)
                # НЕ continue — просто пропускаем уведомления для этого курса
            else:
                stored_hash = fresh_record.get("page_hash")
                
                # Миграция старого хеша на новую схему — без уведомлений
                if stored_hash and stored_hash == get_course_hash_v1(anns) and stored_hash != new_hash:
                    fresh_ann[url] = {"page_hash": new_hash, "last_found": int(time.time())}
                    save_json(ANNOUNCEMENTS_FILE, fresh_ann)
                    # НЕ continue — просто пропускаем уведомления
                # Реальное изменение — уведомляем
                elif not matches_existing_hash(anns, stored_hash):
                    any_new = True
                    fresh_ann[url] = {"page_hash": new_hash, "last_found": int(time.time())}
                    save_json(ANNOUNCEMENTS_FILE, fresh_ann)
                    await bot.send_message(chat_id, f"🔔 Новое объявление в «{course_name}»!")

    await session.close()

    if not any_new:
        await bot.send_message(
            chat_id,
            "✅ Новых объявлений нет.",
            reply_markup=main_menu_keyboard()
        )


@router.message(lambda m: m.text == "🔍 Проверить объявления")
async def manual_check(message: Message):
    """Ручная проверка по кнопке."""
    # Проверка авторизации
    users = load_json(USER_DATA_FILE, {})
    if str(message.chat.id) not in users:
        await message.answer(
            "⚠️ Сначала авторизуйтесь с помощью /login",
            reply_markup=login_keyboard()
        )
        return

    # Препятствуем двойному запуску для одного чата
    lock = get_lock(f"check:{message.chat.id}")
    if lock.locked():
        await message.answer("⏳ Уже проверяю. Подождите пару секунд...")
        return

    async with lock:
        await message.answer("⏳ Проверяю объявления...")
        await check_and_notify(message.chat.id, message.bot)