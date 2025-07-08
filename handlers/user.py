from aiogram import Router, types
from aiogram.filters import Command
from aiogram import F
from aiogram.types import CallbackQuery
from sqlalchemy import select
from datetime import datetime, timedelta
from typing import Union

from database.db import AsyncSessionLocal
from database.models import Lecture
from services.filters import get_lectures
from keyboards.inline import km_directions, km_courses, km_subjects, km_date_templates, km_material_type_templates
from keyboards.reply import main_menu_keyboard
import state_mgr

get_state = state_mgr.get_state
set_state = state_mgr.set_state
clear_state = state_mgr.clear_state

router = Router()


@router.message(F.text == "🔍 Найти конспект")
async def find_flow(msg: types.Message) -> None:
    # Сбрасываем состояние перед началом поиска
    set_state(msg.from_user.id, {})

    await msg.answer(
        "Выберите направление:",
        reply_markup=km_directions()
    )

@router.callback_query(F.data.startswith("dir_"))
async def dir_chosen(cb: CallbackQuery) -> None:
    data = get_state(cb.from_user.id)
    data['direction'] = cb.data.split('_', 1)[1]
    set_state(cb.from_user.id, data)

    await cb.message.answer(
        "Выберите курс:",
        reply_markup=km_courses()
    )
    await cb.answer()

@router.callback_query(F.data.startswith("course_"))
async def course_chosen(cb: CallbackQuery) -> None:
    data = get_state(cb.from_user.id)
    if 'direction' not in data:
        await cb.answer("Сначала выберите направление", show_alert=True)
        return

    data['course'] = int(cb.data.split('_', 1)[1])
    set_state(cb.from_user.id, data)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Lecture.subject)
            .where(
                Lecture.direction == data['direction'],
                Lecture.course    == data['course']
            )
            .distinct()
        )
    subjects = [row[0] for row in result.all()]

    if not subjects:
        await cb.message.answer("⚠️ По выбранному направлению и курсу конспекты не найдены")
        await cb.message.answer("Главное меню:", reply_markup=main_menu_keyboard())
        clear_state(cb.from_user.id)
        return

    await cb.message.answer(
        "Выберите предмет:",
        reply_markup=km_subjects(subjects)
    )
    await cb.answer()

@router.callback_query(F.data.startswith("subject_"))
async def subject_chosen(cb: CallbackQuery) -> None:
    data = get_state(cb.from_user.id)
    if not all(k in data for k in ('direction', 'course')):
        await cb.answer("Сначала выберите направление и курс", show_alert=True)
        return

    data['subject'] = cb.data.split('_', 1)[1]
    set_state(cb.from_user.id, data)

    await cb.message.answer(
        "Выберите необходимый тип материала",
        reply_markup=km_material_type_templates()
    )
    await cb.answer()

@router.callback_query(F.data.startswith("material_type_"))
async def material_type_chosen(cb: CallbackQuery) -> None:
    data = get_state(cb.from_user.id)
    if not all(k in data for k in ('direction', 'course', 'subject')):
        await cb.answer("Сначала выберите направление и курс", show_alert=True)
        return

    data['material_type'] = cb.data.split('_', 2)[2]
    set_state(cb.from_user.id, data)

    await cb.message.answer(
        "Выберите интервал или введите вручную:",
        reply_markup=km_date_templates()
    )
    await cb.message.answer("Или введите две даты: YYYY-MM-DD YYYY-MM-DD")
    await cb.answer()

@router.callback_query(F.data.startswith("range_"))
async def date_template(cb: CallbackQuery) -> None:
    data = get_state(cb.from_user.id)
    if not all(k in data for k in ('direction', 'course', 'subject', 'material_type')):
        await cb.answer("Сначала завершите выбор фильтров", show_alert=True)
        return

    key = cb.data.split('_', 1)[1]
    now = datetime.now()
    if key == 'week':
        start = now - timedelta(weeks=1)
    elif key == 'month':
        start = now - timedelta(days=30)
    else:  # 'year'
        start = now - timedelta(days=365)

    await send_results(cb, start, now)
    await cb.answer()

@router.message()
async def date_manual(msg: types.Message) -> None:
    data = get_state(msg.from_user.id)
    if not all(k in data for k in ('direction', 'course', 'subject', 'material_type')):
        return

    parts = msg.text.strip().split()
    if len(parts) != 2:
        return

    try:
        start = datetime.fromisoformat(parts[0])
        end   = datetime.fromisoformat(parts[1])
    except ValueError:
        await msg.answer("Неверный формат. Введите: YYYY-MM-DD YYYY-MM-DD")
        return

    await send_results(msg, start, end)

async def send_results(origin: Union[types.Message, CallbackQuery], start: datetime, end: datetime) -> None:
    if isinstance(origin, CallbackQuery):
        uid = origin.from_user.id
        send   = origin.message.answer_document
        notify = origin.message.answer
    else:
        uid = origin.from_user.id
        send   = origin.answer_document
        notify = origin.answer

    data = get_state(uid)
    async with AsyncSessionLocal() as session:
        lectures = await get_lectures(
            session,
            data['direction'],
            data['course'],
            data['subject'],
            data['material_type'],
            start,
            end
        )

    if not lectures:
        await notify(
            "По заданным параметрам ничего не найдено.",
            reply_markup=main_menu_keyboard()
        )
    else:
        for lec in lectures:
            await send(lec.file_id, caption=f"{lec.subject} — {lec.date}")
        await notify("Возвращаемся в главное меню", reply_markup=main_menu_keyboard())

    clear_state(uid)