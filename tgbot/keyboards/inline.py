from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_keyboard_with_nums(num_of_buttons: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    [builder.add(InlineKeyboardButton(text=str(num), callback_data=str(num))) for num in range(1, num_of_buttons + 1)]
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
