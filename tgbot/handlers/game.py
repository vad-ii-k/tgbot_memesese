import os
from dataclasses import dataclass
from random import shuffle
from typing import List

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.methods import send_photo, send_message
from aiogram.types import Message, FSInputFile, KeyboardButton, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from html2image import Html2Image
from jinja2 import Environment, FileSystemLoader

player_router = Router()


@dataclass
class Player:
    id: int
    name: str
    cards: List[int]


@dataclass
class SelectedCard:
    num: int
    player_name: str


room_is_active: bool = False
players: List[Player] = []
memes_deck: List[int] = [i for i in range(200)]
situations_deck: List[int] = [i for i in range(100)]
num_of_players: int = 0
selected_cards: List[SelectedCard] = []


@player_router.message(commands=["new_game"], state="*")
async def new_game(message: Message, state: FSMContext):
    global room_is_active
    if not room_is_active:
        room_is_active = True
        await state.set_state("creating")
        builder = ReplyKeyboardBuilder()
        for num in range(1, 9):
            builder.add(KeyboardButton(text=str(num)))
        await message.answer(
            text="Выберите количество игроков:",
            reply_markup=builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
        )
    else:
        await login(message, state)


@player_router.message(state="creating")
async def login(message: Message, state: FSMContext):
    global num_of_players
    if num_of_players == 0:
        num_of_players = int(message.text)
    elif num_of_players == len(players):
        await message.answer("Вы лишний(")
    await state.set_state("entry")
    await message.answer("Введите имя:")


async def send_message_all_players(text: str):
    for player in players:
        await send_message.SendMessage(chat_id=player.id, text=text)


async def send_image_all_players(path: str):
    for player in players:
        await send_photo.SendPhoto(chat_id=player.id, photo=FSInputFile(path=path))


@player_router.message(state="entry")
async def waiting_players(message: Message, state: FSMContext):
    await state.set_state("waiting")
    players.append(Player(message.from_user.id, message.text, []))
    players_list = '\n'.join([' - ' + player.name for player in players])
    if len(players) < num_of_players:
        await state.set_state("gaming")
        message_text = "Ожидание других игроков...\n"\
                       f"Подключилось игроков: {len(players)}/{num_of_players}\n"\
                       f"Список: \n{players_list}"
        await send_message_all_players(message_text)
    elif len(players) == num_of_players:
        await state.set_state("gaming")
        message_text = "Все игроки подключились!\n" \
                       f"Список: \n{players_list}"
        await send_message_all_players(message_text)
        shuffle(memes_deck)
        shuffle(situations_deck)
        await init_card_draw()


async def mailing_templates(situation: int, player: Player):
    results_filename = f"data/compiled_html_pages/html/{player.id}.html"
    environment = Environment(loader=FileSystemLoader("data/html_templates"))
    results_template = environment.get_template("player_side_view.html")

    cards_abspath = os.path.abspath("data/cards")
    with open(results_filename, mode="w", encoding="utf-8") as results:
        results.write(results_template.render(situation=situation, memes=player.cards, cards_abspath=cards_abspath))

    hti = Html2Image(size=(1000, 1100), output_path="data/compiled_html_pages/png/")
    hti.screenshot(html_file=results_filename, save_as=f"{player.id}.png")

    builder = InlineKeyboardBuilder()
    for num in range(1, 7):
        builder.add(InlineKeyboardButton(text=str(num), callback_data=str(num)))

    await send_photo.SendPhoto(
        chat_id=player.id,
        photo=FSInputFile(path=f"data/compiled_html_pages/png/{player.id}.png"),
        reply_markup=builder.as_markup()
    )


async def init_card_draw():
    await send_message_all_players("Игра началась!")
    situation = situations_deck.pop()
    for player in players:
        player.cards = [memes_deck.pop() for num in range(6)]
        await mailing_templates(situation, player)


@player_router.callback_query()
async def meme_choice_handler(callback: CallbackQuery):
    await callback.message.delete_reply_markup()
    await callback.answer(text="Ожидайте других игроков...", cache_time=1)
    for player in players:
        if callback.from_user.id == player.id:
            selected_cards.append(SelectedCard(num=player.cards.pop(int(callback.data)-1), player_name=player.name))
            if len(selected_cards) == num_of_players:
                results_filename = "data/compiled_html_pages/html/showdown.html"
                environment = Environment(loader=FileSystemLoader("data/html_templates"))
                results_template = environment.get_template("showdown_template.html")

                cards_abspath = os.path.abspath("data/cards")
                with open(results_filename, mode="w", encoding="utf-8") as results:
                    results.write(results_template.render(memes=selected_cards, cards_abspath=cards_abspath))

                hti = Html2Image(size=(1000, 900), output_path="data/compiled_html_pages/png/")
                hti.screenshot(html_file=results_filename, save_as="showdown.png")
                await send_image_all_players("data/compiled_html_pages/png/showdown.png")


@player_router.message(commands=["continue"], state="gaming")
async def next_card_draw(message: Message):
    await send_message_all_players("Следующий раунд!")
    selected_cards.clear()
    situation = situations_deck.pop()
    for player in players:
        player.cards.append(memes_deck.pop())
        await mailing_templates(situation, player)


@player_router.message(commands=["finish_game"], state="*")
async def next_card_draw(message: Message, state: FSMContext):
    global room_is_active, memes_deck, situations_deck, num_of_players, selected_cards
    room_is_active = False
    await state.clear()
    await send_message_all_players("Игра закончена, можете начать новую!")
    players.clear()
    memes_deck = [i for i in range(200)]
    situations_deck = [i for i in range(100)]
    num_of_players = 0
    selected_cards.clear()
