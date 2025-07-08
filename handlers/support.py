from aiogram import Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from keyboards.reply import settings_menu_keyboard

router = Router()

@router.message(lambda m: m.text == "💙 Поддержать проект")
async def support_info(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Показать номер карты", callback_data="show_card")],
        [InlineKeyboardButton(text="⭐️ Лайк на Каксе", url="https://share.google/zk8RR53vNLILuxjs6")]
    ])
    await message.answer("📢 Как поддержать бота?", reply_markup=kb)

@router.callback_query(lambda c: c.data == "show_card")
async def show_card(call: CallbackQuery):
    await call.message.answer("💳 2200 2402 2327 2267", reply_markup=settings_menu_keyboard())