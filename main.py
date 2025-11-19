import asyncio
import json
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

# ----------------- НАСТРОЙКИ -----------------

BOT_TOKEN = '8512394178:AAHvqYr-aitTLydXB4x6F50-XQQ7yLRk0f8'

GAME_MODE = "Название режима"
GAME_MAP = "Название карты"
CHAT_LINK = "https://t.me/+bRzRm8Og3aYxNDRi м кеы"

# чат + топик, куда отправлять профиль игрока
PARTY_GROUP_ID = -1002855678816
TOPIC_ID = 45


# ----------------- Работа с ID -----------------

def load_last_id():
    """Загружает последний ID из файла"""
    try:
        with open("players.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("last_id", 0)
    except FileNotFoundError:
        return 0


def save_last_id(last_id):
    """Сохраняет последний ID в файл"""
    with open("players.json", "w", encoding="utf-8") as f:
        json.dump({"last_id": last_id}, f, ensure_ascii=False, indent=4)


last_player_id = load_last_id()


# ----------------- Состояния -----------------

class RegStates(StatesGroup):
    name = State()
    bans = State()


# ----------------- Хендлеры -----------------

async def start_cmd(message: types.Message, state: FSMContext):
    await message.answer("Привет! Напиши своё игровое имя:")
    await state.set_state(RegStates.name)


async def name_input(message: types.Message, state: FSMContext):
    global last_player_id

    name = message.text

    # Генерируем уникальный ID и сохраняем
    last_player_id += 1
    save_last_id(last_player_id)

    await state.update_data(name=name, pid=last_player_id)

    await message.answer(
        f"Твой ID: <b>{last_player_id}</b>\n"
        f"Теперь напиши героев, которых хочешь забанить во всем турнире через запятую (самые частые баны попадут в бан лист)\n",
        parse_mode="HTML"
    )

    await state.set_state(RegStates.bans)


async def bans_input(message: types.Message, state: FSMContext):
    bot = message.bot
    data = await state.get_data()

    name = data["name"]
    pid = data["pid"]
    bans = message.text

    # Telegram username
    username = message.from_user.username
    if username:
        username = f"@{username}"
    else:
        username = "Нет username"

    # Сообщение игроку
    await message.answer(
        f"<b>Регистрация завершена!</b>\n\n"
        f"Имя: {name}\n"
        f"ID: {pid}\n"
        f"Баны: {bans}\n\n"
        f"Чат в котором будет вся информация(Обязательно подписаться!): {CHAT_LINK}",
        parse_mode="HTML"
    )

    # Отправляем профиль игрока в топик
    await bot.send_message(
        chat_id=PARTY_GROUP_ID,
        message_thread_id=TOPIC_ID,
        text=(
            f"🆕 <b>Новый игрок зарегистрирован!</b>\n\n"
            f"👤 Имя: <b>{name}</b>\n"
            f"🆔 ID: <b>{pid}</b>\n"
            f"📛 Telegram: {username}\n"
            f"🚫 Баны: {bans}"
        ),
        parse_mode="HTML"
    )

    await state.clear()


# ----------------- Запуск -----------------

async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.register(start_cmd, Command("start"))
    dp.message.register(name_input, RegStates.name)
    dp.message.register(bans_input, RegStates.bans)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

