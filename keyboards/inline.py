from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def km_directions() -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text="Экономика", callback_data="dir_Экономика"),
        InlineKeyboardButton(text="Менеджмент", callback_data="dir_Менеджмент")
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])

def km_courses() -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text=str(i), callback_data=f"course_{i}") for i in range(1, 5)
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])

def km_subjects(options: list[str]) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text=s, callback_data=f"subject_{s}") for s in options
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])

def km_date_templates() -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text="Последняя неделя", callback_data="range_week"),
        InlineKeyboardButton(text="Последний месяц", callback_data="range_month"),
        InlineKeyboardButton(text="Весь год", callback_data="range_year")
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])

def km_material_type_templates() -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text="лекция", callback_data="material_type_лекция"),
        InlineKeyboardButton(text="семинар", callback_data="material_type_семинар"),
        InlineKeyboardButton(text="доп. материалы", callback_data="material_type_материалы")
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])