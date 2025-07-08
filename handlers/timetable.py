from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup  # Добавлен StatesGroup
from aiogram.filters import Command, StateFilter  # Добавлен StateFilter
from config import SCHEDULE_FILE
import csv
from datetime import datetime, timedelta
from keyboards.reply import main_menu_keyboard, period_keyboard

router = Router()


# Исправлено: используем StatesGroup для корректной работы FSM
class ScheduleStates(StatesGroup):
    waiting_for_group = State()
    waiting_for_period = State()
    waiting_for_type = State()


@router.message(F.text == "📅 Узнать расписание")
@router.message(Command("get_schedule"))
async def show_timetable(message: types.Message, state: FSMContext):
    """Начало процесса получения расписания"""
    await message.answer(
        "Введите номер группы (например, м401 или э201):",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(ScheduleStates.waiting_for_group)


# Исправлено: используем StateFilter для корректной фильтрации состояний
@router.message(StateFilter(ScheduleStates.waiting_for_group))
async def process_group(message: types.Message, state: FSMContext):
    """Обработка номера группы"""
    group = message.text.strip().lower()
    await state.update_data(group=group)
    await message.answer(
        "Выберите период:",
        reply_markup=period_keyboard()
    )
    await state.set_state(ScheduleStates.waiting_for_period)


# Исправлено: правильный фильтр состояния + обработка кнопок
@router.message(StateFilter(ScheduleStates.waiting_for_period))
async def process_period(message: types.Message, state: FSMContext):
    """Обработка выбранного периода"""
    period = message.text.strip()
    valid_periods = ["Сегодня", "Неделя", "Месяц", "Все"]

    if period not in valid_periods:
        await message.answer("Пожалуйста, используйте кнопки для выбора периода!", reply_markup=period_keyboard())
        return

    await state.update_data(period=period)
    await message.answer(
        "Введите тип занятия (Лекция, Семинар, Лаб.работа) или отправьте /skip для всех типов:",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(ScheduleStates.waiting_for_type)


# Исправлено: объединение обработчиков типа занятия
@router.message(Command("skip"), StateFilter(ScheduleStates.waiting_for_type))
@router.message(StateFilter(ScheduleStates.waiting_for_type))
async def process_type(message: types.Message, state: FSMContext):
    """Обработка типа занятия"""
    type_filter = None
    if message.text != "/skip":
        type_filter = message.text.strip()

    # Получаем данные из состояния
    user_data = await state.get_data()
    group = user_data.get("group", "")
    period = user_data.get("period", "Все")

    try:
        schedule_entries = []
        today = datetime.now().date()

        with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';', quotechar='"')
            for row in reader:
                groups = [g.strip().lower() for g in row['Группы'].split(',')]

                if group not in groups:
                    continue

                if type_filter and type_filter.lower() not in row['Тип занятия'].lower():
                    continue

                try:
                    lesson_date = datetime.strptime(row['Дата'], '%d.%m.%Y').date()
                except ValueError:
                    continue

                if period == "Сегодня" and lesson_date != today:
                    continue
                elif period == "Неделя":
                    week_end = today + timedelta(days=7)
                    if lesson_date < today or lesson_date > week_end:
                        continue
                elif period == "Месяц" and (lesson_date.month != today.month or lesson_date.year != today.year):
                    continue

                schedule_entries.append({
                    'date': row['Дата'],
                    'time': row['Время'],
                    'audience': row['Аудитория'],
                    'subject': row['Дисциплина'],
                    'type': row['Тип занятия'],
                    'teacher': row['Преподаватели']
                })

        if not schedule_entries:
            await message.answer(
                "Занятий не найдено!",
                reply_markup=main_menu_keyboard()
            )
            await state.clear()
            return

        # Формируем сообщения частями
        MAX_MESSAGE_LENGTH = 4096
        response_parts = []
        current_part = f"📅 Расписание для группы {group.upper()} ({period}):\n"

        for entry in schedule_entries:
            entry_text = (
                f"\n🗓 {entry['date']} | 🕒 {entry['time']} | 🏫 {entry['audience']}"
                f"\n📚 {entry['type']}: {entry['subject']}"
                f"\n👤 Преподаватель: {entry['teacher']}\n"
                f"{'-' * 30}"
            )

            # Если добавление новой записи превысит лимит
            if len(current_part) + len(entry_text) > MAX_MESSAGE_LENGTH:
                response_parts.append(current_part)
                current_part = entry_text
            else:
                current_part += entry_text

        # Добавляем последнюю часть
        response_parts.append(current_part)

        # Отправляем все части кроме последней без клавиатуры
        for part in response_parts[:-1]:
            await message.answer(part)

        # Последнюю часть отправляем с клавиатурой
        await message.answer(
            response_parts[-1],
            reply_markup=main_menu_keyboard()
        )

    except FileNotFoundError:
        await message.answer(
            "Файл расписания не найден! Ожидайте загрузки.",
            reply_markup=main_menu_keyboard()
        )
    except Exception as e:
        await message.answer(
            f"Произошла ошибка: {str(e)}",
            reply_markup=main_menu_keyboard()
        )
    finally:
        await state.clear()