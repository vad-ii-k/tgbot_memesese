import os
from dataclasses import dataclass
from random import shuffle
from typing import List

from aiogram.methods import send_message, send_photo
from aiogram.types import FSInputFile
from aiogram.utils.i18n import gettext as _
from jinja2 import Environment, FileSystemLoader
from pyppeteer import launch

from tgbot.keyboards.inline import get_keyboard_with_nums


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
            player.cards = [self.memes_deck.pop() for _i in range(6)]
            await self.create_player_side_view_photo(situation, player)
            await self.send_player_side_view_message(player)

    async def create_player_side_view_photo(self, situation: int, player: Player):
        results_filename = f"data/compiled_html_pages/html/{player.id}.html"
        environment = Environment(loader=FileSystemLoader("data/html_templates"))
        results_template = environment.get_template("player_side_view.html")

        cards_abspath = os.path.abspath("data/cards")
        with open(results_filename, mode="w", encoding="utf-8") as results:
            results.write(results_template.render(
                players=self.players,
                situation=situation,
                memes=player.cards,
                cards_abspath=cards_abspath
            ))

        browser_for_psv = await launch(defaultViewport={'width': 1000, 'height': 1100})
        page_for_psv = await browser_for_psv.newPage()
        await page_for_psv.goto(f'file:///{os.path.abspath(f"data/compiled_html_pages/html/{player.id}.html")}')
        await page_for_psv.screenshot(
            path=f'data/compiled_html_pages/png/{player.id}.png',
            type='jpeg',
            fullPage=True,
            quality=100
        )
        await browser_for_psv.close()

    @staticmethod
    async def send_player_side_view_message(player: Player):
        await send_photo.SendPhoto(
            chat_id=player.id,
            photo=FSInputFile(path=f"data/compiled_html_pages/png/{player.id}.png"),
            reply_markup=get_keyboard_with_nums(num_of_buttons=6),
            caption=_("Выберите мем ⬇")
        )

    async def create_showdown_photo(self):
        results_filename = "data/compiled_html_pages/html/showdown.html"
        environment = Environment(loader=FileSystemLoader("data/html_templates"))
        results_template = environment.get_template("showdown_template.html")

        cards_abspath = os.path.abspath("data/cards")
        with open(results_filename, mode="w", encoding="utf-8") as results:
            results.write(results_template.render(memes=self.selected_cards, cards_abspath=cards_abspath))

        browser_for_sd = await launch(defaultViewport={'width': 1000, 'height': 1100})
        page_for_sd = await browser_for_sd.newPage()
        await page_for_sd.goto(f'file:///{os.path.abspath("data/compiled_html_pages/html/showdown.html")}')
        await page_for_sd.screenshot(
            path='data/compiled_html_pages/png/showdown.png',
            type='jpeg',
            fullPage=True,
            quality=100
        )
        await browser_for_sd.close()
