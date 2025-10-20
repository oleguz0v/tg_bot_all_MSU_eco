import asyncio
import logging
import time

from aiogram import Bot, Dispatcher
from config import TOKEN, USER_DATA_FILE, ANNOUNCEMENTS_FILE
from database.db import init_db
from utils.storage import load_json, save_json
from utils.auth import login
from utils.parser import get_announcements
from utils.hashing import get_course_hash, get_course_hash_v1, matches_existing_hash
from utils.locks import get_lock

# Импортируем все роутеры
from handlers import (
    start, login as login_handler, courses, announcements,
    change, support, stop, timetable, user, contacts, settings,
    admin
)


async def periodic_check(bot: Bot):
    """Фоновая проверка всех курсов каждые 10 минут."""
    while True:
        logging.info("Starting periodic check of announcements...")

        users = load_json(USER_DATA_FILE, {})
        ann = load_json(ANNOUNCEMENTS_FILE, {})

        # Собираем подписчиков по URL курса
        subs_map = {}
        for uid, user_data in users.items():
            for course_name in user_data.get("subscriptions", []):
                url = user_data.get("available_courses", {}).get(course_name)
                if url:
                    subs_map.setdefault(url, []).append((uid, course_name))

        # Проверяем каждый курс
        for url, subs in subs_map.items():
            if not subs:
                continue

            first_uid, _ = subs[0]
            first_user = users.get(first_uid)
            if not first_user:
                continue

            session = await login(first_user["username"], first_user["password"])
            if not session:
                logging.error(f"Auth failed for course {url}")
                continue

            try:
                anns = await get_announcements(session, url)
                if not anns:
                    continue
                new_hash = get_course_hash(anns)
            except Exception as e:
                logging.error(f"Error getting announcements for {url}: {e}")
                continue
            finally:
                await session.close()

            now_ts = int(time.time())

            # Вся логика проверки и обновления под одним URL-локом
            url_lock = get_lock(f"url:{url}")
            async with url_lock:
                fresh_ann = load_json(ANNOUNCEMENTS_FILE, {})
                fresh_record = fresh_ann.get(url)
                
                # Первая инициализация без уведомлений
                if fresh_record is None:
                    fresh_ann[url] = {"page_hash": new_hash, "last_found": now_ts}
                    save_json(ANNOUNCEMENTS_FILE, fresh_ann)
                    # НЕ continue — просто пропускаем уведомления для этого курса
                else:
                    stored_hash = fresh_record.get("page_hash")

                    # Миграция старого хеша на новую схему — без уведомлений
                    if stored_hash and stored_hash == get_course_hash_v1(anns) and stored_hash != new_hash:
                        fresh_ann[url] = {"page_hash": new_hash, "last_found": now_ts}
                        save_json(ANNOUNCEMENTS_FILE, fresh_ann)
                        # НЕ continue — просто пропускаем уведомления
                    # Реальное изменение — обновляем и уведомляем
                    elif not matches_existing_hash(anns, stored_hash):
                        fresh_ann[url] = {"page_hash": new_hash, "last_found": now_ts}
                        save_json(ANNOUNCEMENTS_FILE, fresh_ann)

                        for chat_id, course_name in subs:
                            try:
                                await bot.send_message(
                                    int(chat_id),
                                    f"🔔 Новое объявление в «{course_name}»!"
                                )
                                if chat_id in users:
                                    users[chat_id]["last_update"] = now_ts
                            except Exception as e:
                                logging.error(f"Error sending to {chat_id}: {e}")

        # Сохраняем обновлённые данные
        save_json(USER_DATA_FILE, users)
        logging.info("Periodic check completed")

        # Ждём до следующего цикла
        await asyncio.sleep(600)


async def on_startup():
    """Действия при запуске бота"""
    await init_db()  # Инициализация БД для конспектов
    logging.info("Database initialized")


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    # Регистрируем все роутеры
    dp.include_router(settings.router)
    dp.include_router(start.router)
    dp.include_router(login_handler.router)
    dp.include_router(courses.router)
    dp.include_router(announcements.router)
    dp.include_router(change.router)
    dp.include_router(support.router)
    dp.include_router(stop.router)
    dp.include_router(timetable.router)
    dp.include_router(contacts.router)
    dp.include_router(user.router)
    dp.include_router(admin.router)

    # Хук при запуске
    dp.startup.register(on_startup)

    # Запускаем фоновые проверки
    asyncio.create_task(periodic_check(bot))

    logging.info("🤖 Объединённый бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())