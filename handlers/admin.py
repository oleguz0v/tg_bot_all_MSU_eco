from aiogram import Router, types, F
from config import CHANNEL_ID, USER_DATA_FILE
from database.db import AsyncSessionLocal
from database.models import Lecture
from datetime import datetime
import os  # Импорт модуля для работы с файловой системой
import asyncio
from utils.storage import load_json

router = Router()


@router.channel_post(F.document)
async def on_channel_pdf(post: types.Message) -> None:
    if post.chat.id != CHANNEL_ID:
        return

    caption = (post.caption or "").strip()

    # 1. Обработка файла расписания
    if caption.lower() == "расписание":
        # Проверяем расширение файла
        if post.document.file_name and post.document.file_name.endswith('.csv'):
            # Скачиваем и сохраняем файл
            file_id = post.document.file_id
            file = await post.bot.get_file(file_id)
            file_path = file.file_path

            # Сохраняем с именем timetable.csv
            destination = "timetable.csv"
            await post.bot.download_file(file_path, destination)

            print(f"Расписание обновлено: {destination}")
        else:
            print("Ошибка: Файл расписания должен быть в формате CSV")
        return  # Выходим после обработки расписания

    # 2. Обработка конспектов (прежняя логика)
    parts = [p.strip() for p in caption.split(";")]
    if len(parts) != 5:
        print("Invalid caption:", caption)
        return

    direction, cs, subject, material_type, ds = parts
    try:
        course = int(cs)
        date = datetime.strptime(ds, "%Y-%m-%d").date()
    except Exception as e:
        print("Parse error:", e)
        return

    subject = subject.lower()
    material_type = material_type.lower()
    async with AsyncSessionLocal() as session:
        lec = Lecture(
            direction=direction,
            course=course,
            subject=subject,
            material_type=material_type,
            date=date,
            channel_msg_id=post.message_id,
            file_id=post.document.file_id
        )
        session.add(lec)
        await session.commit()
    print("Saved lecture:", direction, course, subject, material_type, date)


@router.channel_post(F.text.startswith("/message_for_everybody"))
async def broadcast_message(post: types.Message) -> None:
    if post.chat.id != CHANNEL_ID:
        return

    full_text = (post.text or "").strip()
    parts = full_text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await post.answer("⚠️ Укажите текст после команды: /message_for_everybody <текст>")
        return

    message_text = parts[1].strip()

    users = load_json(USER_DATA_FILE, {})
    chat_ids = list(users.keys())

    sent = 0
    for uid in chat_ids:
        try:
            await post.bot.send_message(int(uid), message_text)
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            # Пропускаем неудачные отправки, не прерывая рассылку
            pass

    await post.answer(f"✅ Сообщение отправлено {sent} пользователям")