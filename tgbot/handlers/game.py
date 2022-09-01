from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from tgbot.game.room import Player, GameRoom, SelectedCard
from tgbot.keyboards.inline import get_keyboard_with_nums

player_router = Router()
room = GameRoom()


@player_router.message(commands=["new_game"], state="*")
async def new_game(message: Message, state: FSMContext):
    if not room.room_is_active:
        room.room_is_active = True
        await state.set_state("creating")
        await message.answer(
            text="🆕 Выберите количество игроков:",
            reply_markup=get_keyboard_with_nums(num_of_buttons=6)
        )
    elif room.num_of_players == 0:
        await message.answer("🔄 Подождите создания комнаты...")
    elif room.num_of_players == len(room.players):
        await message.answer("🛑 Вы лишний!")
    else:
        await login(message, state)


@player_router.callback_query(state="creating")
async def set_num_of_players(callback: CallbackQuery, state: FSMContext):
    room.num_of_players = int(callback.data)
    await callback.answer(text="✅ Комната создана!", cache_time=1)
    await callback.message.delete()
    await login(callback.message, state)


async def login(message: Message, state: FSMContext):
    await state.set_state("entry")
    await message.answer("🔤 Введите имя:")


@player_router.message(state="entry")
async def waiting_players(message: Message, state: FSMContext):
    room.players.append(Player(message.from_user.id, message.text, []))
    players_list = '\n'.join(['  ➖  ' + player.name for player in room.players])
    await state.set_state("gaming")
    if len(room.players) < room.num_of_players:
        message_text = "⏳ Ожидание других игроков...\n" \
                       f"ℹ️ Подключилось игроков: {len(room.players)}/{room.num_of_players}\n" \
                       f"*️⃣ Список: \n{players_list}"
        await room.send_message_all_players(message_text)
    else:
        message_text = "✅ Все игроки подключились!\n" \
                       f"*️⃣ Список: \n{players_list}"
        await room.send_message_all_players(message_text)
        await room.init_card_draw()


@player_router.callback_query()
async def meme_choice_handler(callback: CallbackQuery):
    await callback.message.delete_reply_markup()
    await callback.message.edit_caption(caption="")
    await callback.answer(text="🔄 Ожидайте других игроков...", cache_time=1)
    for player in room.players:
        if callback.from_user.id == player.id:
            room.selected_cards.append(SelectedCard(num=player.cards.pop(int(callback.data)-1), player_name=player.name))
            if len(room.selected_cards) == room.num_of_players:
                await room.create_showdown_photo()
                await room.send_image_all_players("data/compiled_html_pages/png/showdown.png")


@player_router.message(commands=["continue"], state="gaming")
async def next_card_draw(message: Message):
    await room.send_message_all_players("⏭ Следующий раунд!")
    room.selected_cards.clear()
    situation = room.situations_deck.pop()
    for player in room.players:
        player.cards.append(room.memes_deck.pop())
        await room.create_player_side_view_photo(situation, player)
        await room.send_player_side_view_message(player)


@player_router.message(commands=["finish_game"], state="gaming")
async def finish_game(message: Message, state: FSMContext):
    global room
    await room.send_message_all_players("🏁 Игра закончена, можете начать новую!")
    room = GameRoom()
    await state.clear()
