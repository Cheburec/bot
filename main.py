import json
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.client.default import DefaultBotProperties

BOT_TOKEN = '8432535237:AAG4S7wyvrOMQe-GpGxXSBhozy10jxkWTEo'

# ID группы и темы форума
PARTY_GROUP_ID = -1002855678816
TOPIC_ID = 45  # ID темы форума

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())

# ---------- СОСТОЯНИЯ ----------
class ProfileForm(StatesGroup):
    position = State()
    mmr = State()
    dota_id = State()
    politeness = State()
    honesty = State()

# ---------- ХРАНИЛИЩЕ ----------
def load_profiles():
    try:
        with open("profiles.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_profiles(profiles):
    with open("profiles.json", "w", encoding="utf-8") as f:
        json.dump(profiles, f, ensure_ascii=False, indent=4)

# ---------- КРАСИВЫЙ ПРОФИЛЬ ----------
def format_profile(profile):
    dota_id = profile["dota_id"]
    dotabuff_url = f"https://www.dotabuff.com/players/{dota_id}"
    opendota_url = f"https://www.opendota.com/players/{dota_id}"
    return (
        f"<b>🎮 Dota профиль</b>\n"
        f"👤 <b>Имя:</b> @{profile.get('username', '—')}\n"
        f"🆔 <b>Dota ID:</b> <code>{dota_id}</code> "
        f"<a href='{dotabuff_url}'>Dotabuff</a> | <a href='{opendota_url}'>OpenDota</a>\n"
        f"🏆 <b>MMR:</b> {profile['mmr']}\n"
        f"🤝 <b>Порядочность:</b> {profile['honesty']} | 😊 <b>Вежливость:</b> {profile['politeness']}\n"
        f"🕹 <b>Роли:</b> {profile['position']}"
    )

# ---------- РОЛИ ----------
positions = ["полная поддержка", "поддержка", "сложная", "центр", "лёгкая"]

def get_positions_keyboard(selected_roles=None):
    selected_roles = selected_roles or []
    buttons = []
    for pos in positions:
        text = f"{'✅ ' if pos in selected_roles else ''}{pos}"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"position_toggle:{pos}")])
    buttons.append([InlineKeyboardButton(text="Готово", callback_data="position_done")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ---------- ПРОФИЛЬ (INLINE) ----------
def profile_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Изменить профиль", callback_data="edit_profile")],
            [InlineKeyboardButton(text="🗑 Очистить профиль", callback_data="clear_profile")]
        ]
    )

# ---------- НИЖНЕЕ МЕНЮ ----------
bottom_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Мой профиль"), KeyboardButton(text="Найти пати")]
    ],
    resize_keyboard=True
)

# ---------- /start ----------
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.update_data(selected_roles=[])
    await message.answer("Выберите одну или несколько ролей:", reply_markup=get_positions_keyboard())
    await message.answer("Меню действий:", reply_markup=bottom_menu)
    await state.set_state(ProfileForm.position)

# ---------- ВЫБОР РОЛЕЙ ----------
@dp.callback_query(lambda c: c.data.startswith("position_toggle:") or c.data == "position_done")
async def choose_positions(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_roles = data.get("selected_roles", [])

    if callback.data.startswith("position_toggle:"):
        pos = callback.data.split(":", 1)[1]
        if pos in selected_roles:
            selected_roles.remove(pos)
        else:
            selected_roles.append(pos)
        await state.update_data(selected_roles=selected_roles)
        await callback.message.edit_reply_markup(reply_markup=get_positions_keyboard(selected_roles))
        await callback.answer()
    elif callback.data == "position_done":
        if not selected_roles:
            await callback.answer("Выберите хотя бы одну роль!")
            return
        await state.update_data(position=", ".join(selected_roles))
        await callback.message.edit_text(f"Вы выбрали роли: {', '.join(selected_roles)}")
        await callback.message.answer("Введите свой MMR (число):")
        await state.set_state(ProfileForm.mmr)
        await callback.answer()

# ---------- СОЗДАНИЕ ПРОФИЛЯ ----------
@dp.message(ProfileForm.mmr)
async def set_mmr(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("MMR должен быть числом.")
        return
    await state.update_data(mmr=int(message.text))
    await message.answer("Введите свой Dota ID (число):")
    await state.set_state(ProfileForm.dota_id)

@dp.message(ProfileForm.dota_id)
async def set_dota_id(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Dota ID должен быть числом.")
        return
    await state.update_data(dota_id=int(message.text))
    await message.answer("Введите количество вежливости (0–12000):")
    await state.set_state(ProfileForm.politeness)

@dp.message(ProfileForm.politeness)
async def set_politeness(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or not (0 <= int(message.text) <= 12000):
        await message.answer("Введите число от 0 до 12000.")
        return
    await state.update_data(politeness=int(message.text))
    await message.answer("Введите количество порядочности (0–12000):")
    await state.set_state(ProfileForm.honesty)

@dp.message(ProfileForm.honesty)
async def set_honesty(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or not (0 <= int(message.text) <= 12000):
        await message.answer("Введите число от 0 до 12000.")
        return
    await state.update_data(honesty=int(message.text))
    data = await state.get_data()

    profiles = load_profiles()
    profiles = [p for p in profiles if p["user_id"] != message.from_user.id]

    profile = {
        "user_id": message.from_user.id,
        "username": message.from_user.username,
        **data
    }

    profiles.append(profile)
    save_profiles(profiles)

    await message.answer("✅ Профиль успешно создан!", reply_markup=bottom_menu)
    await message.answer(format_profile(profile), reply_markup=profile_menu())
    await state.clear()

# ---------- ПОКАЗ ПРОФИЛЯ ----------
@dp.message(Command("профиль"))
async def show_profile(message: types.Message):
    profiles = load_profiles()
    profile = next((p for p in profiles if p["user_id"] == message.from_user.id), None)
    if not profile:
        await message.answer("😕 Профиль не найден. Используй /start, чтобы создать его.")
        return
    await message.answer(format_profile(profile), reply_markup=profile_menu())

# ---------- НИЖНЕЕ МЕНЮ ----------
@dp.message()
async def bottom_menu_handler(message: types.Message):
    if message.text == "Мой профиль":
        profiles = load_profiles()
        profile = next((p for p in profiles if p["user_id"] == message.from_user.id), None)
        if not profile:
            await message.answer("😕 Профиль не найден. Используй /start, чтобы создать его.")
            return
        await message.answer(format_profile(profile), reply_markup=profile_menu())

    elif message.text == "Найти пати":
        profiles = load_profiles()
        profile = next((p for p in profiles if p["user_id"] == message.from_user.id), None)
        if not profile:
            await message.answer("😕 Профиль не найден. Создай его через /start.")
            return

        # Добавляем кнопку удаления
        delete_button = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🗑 Удалить анкету", callback_data=f"delete_{profile['user_id']}")]
            ]
        )

        sent_message = await bot.send_message(
            chat_id=PARTY_GROUP_ID,
            message_thread_id=TOPIC_ID,
            text=f"🔔 Новый игрок ищет пати!\n\n{format_profile(profile)}",
            reply_markup=delete_button
        )

        # Сохраняем ID сообщения для возможности удаления
        profile["post_message_id"] = sent_message.message_id
        save_profiles(profiles)

        message_link = f"https://t.me/c/{str(PARTY_GROUP_ID)[4:]}/{sent_message.message_id}"
        await message.answer(f"✅ Ваша анкета опубликована!\n🔗 {message_link}")

# ---------- УДАЛЕНИЕ АНКЕТЫ ----------
@dp.callback_query(lambda c: c.data.startswith("delete_"))
async def delete_profile_post(callback: types.CallbackQuery):
    user_id_in_callback = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    if user_id != user_id_in_callback:
        await callback.answer("⛔ Это не ваша анкета!", show_alert=True)
        return

    profiles = load_profiles()
    profile = next((p for p in profiles if p["user_id"] == user_id), None)
    if not profile or "post_message_id" not in profile:
        await callback.answer("⚠️ Анкета не найдена или уже удалена.", show_alert=True)
        return

    try:
        await bot.delete_message(chat_id=PARTY_GROUP_ID, message_id=profile["post_message_id"])
        profile.pop("post_message_id", None)
        save_profiles(profiles)
        await callback.message.answer("🗑 Ваша анкета удалена из чата.")
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка при удалении: {e}")

# ---------- INLINE ----------
@dp.callback_query(lambda c: c.data == "clear_profile")
async def clear_profile(callback: types.CallbackQuery):
    profiles = load_profiles()
    profiles = [p for p in profiles if p["user_id"] != callback.from_user.id]
    save_profiles(profiles)
    await callback.message.edit_text("🗑 Профиль очищен.")
    await callback.answer("Удалено!")

@dp.callback_query(lambda c: c.data == "edit_profile")
async def edit_profile(callback: types.CallbackQuery):
    await callback.message.answer("Чтобы изменить профиль — используй /start заново.")
    await callback.answer()

# ---------- ЗАПУСК ----------
async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

