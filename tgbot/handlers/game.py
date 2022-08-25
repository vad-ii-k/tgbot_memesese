from dataclasses import dataclass
from random import shuffle
from typing import List

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.methods import send_photo, send_message
from aiogram.types import Message, FSInputFile, ReplyKeyboardMarkup, KeyboardButton


player_router = Router()


@dataclass
class Player:
    id: int
    name: str


room_is_active: bool = False
players: List[Player] = []
deck: List[int] = [i for i in range(10)]
num_of_players: int = 0


@player_router.message(commands=["new_game"], state="*")
async def new_game(message: Message, state: FSMContext):
    global room_is_active
    if not room_is_active:
        room_is_active = True
        await state.set_state("creating")
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text='1'),
                       KeyboardButton(text='2'),
                       KeyboardButton(text='3'),
                       KeyboardButton(text='4'),
                       KeyboardButton(text='5'),
                       KeyboardButton(text='6'),
                       KeyboardButton(text='7')]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await message.answer(
            text="Выберите количество игроков:",
            reply_markup=keyboard
        )
    else:
        await login(message, state)


@player_router.message(state="creating")
async def login(message: Message, state: FSMContext):
    global num_of_players
    if num_of_players == 0:
        num_of_players = int(message.text)
    await state.set_state("entry")
    await message.answer("Введите имя:")


async def send_message_all_players(text: str):
    for player in players:
        await send_message.SendMessage(chat_id=player.id, text=text)


@player_router.message(state="entry")
async def waiting_players(message: Message, state: FSMContext):
    await state.set_state("waiting")
    players.append(Player(message.from_user.id, message.text))
    if len(players) < num_of_players:
        players_list = '\n'.join([' - ' + player.name for player in players])
        message_text = "Ожидание других игроков...\n"\
                       f"Подключилось игроков: {len(players)}/{num_of_players}\n"\
                       f"Список: \n{players_list}"
        await send_message_all_players(message_text)
    elif len(players) == num_of_players:
        await state.set_state("gaming")
        shuffle(deck)
        await card_draw()
    else:
        players.pop()
        await message.answer("Вы лишний(")


async def card_draw():
    await send_message_all_players("Игра началась!")
    for player in players:
        await send_photo.SendPhoto(chat_id=player.id, photo=FSInputFile(path=f"data/images/{deck.pop()}.png"))
