import time
from aiogram import Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from utils.storage import load_json, save_json
from utils.auth import login
from utils.parser import get_courses, get_announcements
from utils.hashing import get_course_hash
from config import USER_DATA_FILE, ANNOUNCEMENTS_FILE
from keyboards.reply import main_menu_keyboard, login_keyboard

router = Router()


async def send_course_selection_keyboard(message: Message):
    """Выводит клавиатуру выбора курсов и сохраняет доступные курсы в файл."""
    chat_id = message.chat.id
    users_data = load_json(USER_DATA_FILE, {})

    # Проверка авторизации
    if str(chat_id) not in users_data:
        await message.answer(
            "⚠️ Вы не авторизованы. Пожалуйста, выполните вход с помощью /login",
            reply_markup=login_keyboard()
        )
        return

    user = users_data[str(chat_id)]
    user["manual_state"] = None
    user.pop("temp_url", None)
    save_json(USER_DATA_FILE, users_data)

    username, password = user["username"], user["password"]
    session = await login(username, password)

    if not session:
        await message.answer(
            "❌ Ошибка авторизации. Проверьте логин и пароль!",
            reply_markup=main_menu_keyboard()
        )
        return

    courses = await get_courses(session)
    await session.close()

    if not courses:
        await message.answer(
            "⚠️ Курсы не найдены. Попробуйте позже.",
            reply_markup=main_menu_keyboard()
        )
        return

    # Сохраняем доступные курсы пользователя
    user["available_courses"] = courses
    users_data[str(chat_id)] = user
    save_json(USER_DATA_FILE, users_data)

    # Формируем клавиатуру
    names = list(courses.keys())
    course_buttons = [
        [KeyboardButton(text=name) for name in names[i: i + 2]]
        for i in range(0, len(names), 2)
    ]
    course_buttons.append([KeyboardButton(text="➕ Добавить курс вручную")])
    course_buttons.append([KeyboardButton(text="✅ Готово")])

    kb = ReplyKeyboardMarkup(keyboard=course_buttons, resize_keyboard=True)
    await message.answer(
        "📚 <b>Выберите курсы</b> (нажмите на название)\n"
        "По окончании нажмите «✅ Готово»:",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.message(lambda m: m.text in load_json(USER_DATA_FILE, {}).get(str(m.chat.id), {}).get("available_courses", {}))
async def toggle_course_subscription(message: Message):
    chat_id = str(message.chat.id)
    users = load_json(USER_DATA_FILE, {})
    user = users[chat_id]
    course_name = message.text
    course_url = user.get("available_courses", {}).get(course_name)

    if course_name in user.get("subscriptions", []):
        user["subscriptions"].remove(course_name)
        text = f"❌ Отписались от «{course_name}»"
    else:
        user.setdefault("subscriptions", []).append(course_name)
        text = f"✅ Подписались на «{course_name}»"
        
        # Инициализация хеша курса под локом, чтобы избежать гонок
        from utils.locks import get_lock
        url_lock = get_lock(f"url:{course_url}")
        async with url_lock:
            ann = load_json(ANNOUNCEMENTS_FILE, {})
            if course_url not in ann:
                session = await login(user["username"], user["password"])
                anns = await get_announcements(session, course_url)
                await session.close()
                h = get_course_hash(anns)
                ann[course_url] = {"page_hash": h, "last_found": int(time.time())}
                save_json(ANNOUNCEMENTS_FILE, ann)

    save_json(USER_DATA_FILE, users)
    await message.answer(text)


@router.message(lambda m: m.text == "✅ Готово")
async def finish_course_selection(message: Message):
    chat_id = str(message.chat.id)
    users = load_json(USER_DATA_FILE, {})
    user = users.get(chat_id)
    if not user or not user.get("subscriptions"):
        return await message.answer("⚠️ Ничего не выбрано.", reply_markup=main_menu_keyboard())
    user["state"] = "main_menu"
    user["manual_state"] = None
    user.pop("temp_url", None)
    save_json(USER_DATA_FILE, users)
    from keyboards.reply import main_menu_keyboard
    await message.answer(
        "✅ Сохранено! Теперь я буду проверять обновления по выбранным курсам каждые 10 минут!",
        reply_markup=main_menu_keyboard()
    )


@router.message(lambda m: m.text == "➕ Добавить курс вручную")
async def ask_manual_url(message: Message):
    """Шаг 1: спрашиваем только URL."""
    uid = str(message.chat.id)
    users = load_json(USER_DATA_FILE, {})
    if uid not in users:
        return await message.answer("⚠️ Сначала /login", reply_markup=main_menu_keyboard())
    users[uid]["manual_state"] = "awaiting_url"
    save_json(USER_DATA_FILE, users)
    await message.answer(
        "🔗 Введите URL курса (должен начинаться с https://on.econ.msu.ru/course/view.php?id=):"
    )


@router.message(lambda m:
                load_json(USER_DATA_FILE, {})
                .get(str(m.chat.id), {})
                .get("manual_state") == "awaiting_url"
                )
async def process_manual_url(message: Message):
    """Шаг 2: получили URL, проверили и сразу подписали или спросили название."""
    uid = str(message.chat.id)
    users = load_json(USER_DATA_FILE, {})
    user = users[uid]

    url = message.text.strip()
    # проверяем формат
    if not url.startswith("https://on.econ.msu.ru/course/view.php?id="):
        return await message.answer("❌ Неверный формат URL. Попробуйте ещё раз.")

    # проверяем доступность: дергаем анонсы
    session = await login(user["username"], user["password"])
    if not session:
        return await message.answer("❌ Ошибка авторизации.")
    anns = await get_announcements(session, url)
    await session.close()

    if len(anns) < 1:
        return await message.answer("❌ Курс недоступен или нет объявлений.")

    # строим глобальную базу URL→name
    global_courses = {
        uurl: nm
        for u in users.values()
        for nm, uurl in u.get("available_courses", {}).items()
    }

    # Если URL уже есть в глобальной базе — сразу подпишем под старым именем
    if url in global_courses:
        name = global_courses[url]
        # добавляем в user.available_courses и подписки
        user.setdefault("available_courses", {})[name] = url
        if name not in user.setdefault("subscriptions", []):
            user["subscriptions"].append(name)
        users[uid] = user
        save_json(USER_DATA_FILE, users)
        return await message.answer(f"✅ Подписка на «{name}» оформлена автоматически.")

    # иначе — новый курс, нужно спросить имя
    user["temp_url"] = url
    user["manual_state"] = "awaiting_name"
    users[uid] = user
    save_json(USER_DATA_FILE, users)
    await message.answer("✏️ URL принят. Теперь введите название курса:")


@router.message(lambda m:
                load_json(USER_DATA_FILE, {})
                .get(str(m.chat.id), {})
                .get("manual_state") == "awaiting_name"
                )
async def process_manual_name(message: Message):
    """Шаг 3: получили название — добавляем новый курс."""
    uid = str(message.chat.id)
    users = load_json(USER_DATA_FILE, {})
    user = users[uid]

    name = message.text.strip()
    url = user.get("temp_url")
    if not url:
        user["manual_state"] = None
        save_json(USER_DATA_FILE, users)
        return await message.answer("⚠️ Что-то пошло не так, попробуйте снова ➕ Добавить курс вручную")

    # сохраняем в user.available_courses + подписки
    user.setdefault("available_courses", {})[name] = url
    if name not in user.setdefault("subscriptions", []):
        user["subscriptions"].append(name)

    # инициализируем announcements.json под локом
    from utils.locks import get_lock
    url_lock = get_lock(f"url:{url}")
    async with url_lock:
        ann = load_json(ANNOUNCEMENTS_FILE, {})
        if url not in ann:
            session = await login(user["username"], user["password"])
            anns = await get_announcements(session, url)
            await session.close()
            h = get_course_hash(anns)
            ann[url] = {"page_hash": h, "last_found": int(time.time())}
            save_json(ANNOUNCEMENTS_FILE, ann)

    # сбрасываем временный state и url
    user["manual_state"] = None
    user.pop("temp_url", None)
    users[uid] = user
    save_json(USER_DATA_FILE, users)

    await message.answer(f"✅ Курс «{name}» добавлен и подписка оформлена.")

    # вернём пользователя в меню выбора
    await send_course_selection_keyboard(message)