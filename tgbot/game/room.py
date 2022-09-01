import os
from dataclasses import dataclass
from random import shuffle
from typing import List

from aiogram.methods import send_message, send_photo
from aiogram.types import FSInputFile, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from html2image import Html2Image
from jinja2 import Environment, FileSystemLoader


@dataclass
class Player:
    id: int
    name: str
    cards: List[int]


@dataclass
class SelectedCard:
    num: int
    player_name: str


class GameRoom:
    def __init__(self):
        self.room_is_active: bool = False
        self.players: List[Player] = []
        self.memes_deck: List[int] = [i for i in range(200)]
        self.situations_deck: List[int] = [i for i in range(100)]
        self.num_of_players: int = 0
        self.selected_cards: List[SelectedCard] = []

    async def send_message_all_players(self, text: str):
        for player in self.players:
            await send_message.SendMessage(chat_id=player.id, text=text)

    async def send_image_all_players(self, path: str):
        for player in self.players:
            await send_photo.SendPhoto(chat_id=player.id, photo=FSInputFile(path=path))

    async def init_card_draw(self):
        shuffle(self.memes_deck)
        shuffle(self.situations_deck)
        await self.send_message_all_players("🔥 Игра началась!")
        situation = self.situations_deck.pop()
        for player in self.players:
            player.cards = [self.memes_deck.pop() for _ in range(6)]
            await self.create_player_side_view_photo(situation, player)
            await self.send_player_side_view_message(player)

    @staticmethod
    async def create_player_side_view_photo(situation: int, player: Player):
        results_filename = f"data/compiled_html_pages/html/{player.id}.html"
        environment = Environment(loader=FileSystemLoader("data/html_templates"))
        results_template = environment.get_template("player_side_view.html")

        cards_abspath = os.path.abspath("data/cards")
        with open(results_filename, mode="w", encoding="utf-8") as results:
            results.write(results_template.render(situation=situation, memes=player.cards, cards_abspath=cards_abspath))

        hti = Html2Image(size=(1000, 1100), output_path="data/compiled_html_pages/png/")
        hti.screenshot(html_file=results_filename, save_as=f"{player.id}.png")

    @staticmethod
    async def send_player_side_view_message(player: Player):
        builder = InlineKeyboardBuilder()
        for num in range(1, 7):
            builder.add(InlineKeyboardButton(text=str(num), callback_data=str(num)))

        await send_photo.SendPhoto(
            chat_id=player.id,
            photo=FSInputFile(path=f"data/compiled_html_pages/png/{player.id}.png"),
            reply_markup=builder.as_markup(),
            caption="Выберите мем ⬇"
        )

    async def create_showdown_photo(self):
        results_filename = "data/compiled_html_pages/html/showdown.html"
        environment = Environment(loader=FileSystemLoader("data/html_templates"))
        results_template = environment.get_template("showdown_template.html")

        cards_abspath = os.path.abspath("data/cards")
        with open(results_filename, mode="w", encoding="utf-8") as results:
            results.write(results_template.render(memes=self.selected_cards, cards_abspath=cards_abspath))

        hti = Html2Image(size=(1000, 900), output_path="data/compiled_html_pages/png/")
        hti.screenshot(html_file=results_filename, save_as="showdown.png")