from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Router
import sqlite3
import asyncio

# Токен вашего бота
API_TOKEN = '7744329125:AAExqDVL1GTnBcFUQdnxoiF7pE4mLMy-waA'

# Инициализация бота, диспетчера и маршрутизатора
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()

# Подключение к базе данных
db_file = "users.db"

def init_db():
    """Инициализация базы данных."""
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE,
        name TEXT,
        phone TEXT
    )
    """)
    conn.commit()
    conn.close()

# Определение состояний
class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()

# Кнопка для отправки номера телефона
phone_button = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Отправить номер телефона", request_contact=True)]],
    resize_keyboard=True
)

# Стартовое сообщение
@router.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        await message.answer(f"Добро пожаловать обратно, {result[2]}!")
    else:
        await message.answer("Привет! Давайте зарегистрируем вас. Пожалуйста, отправьте ваше имя.")
        await state.set_state(RegistrationStates.waiting_for_name)

# Получение имени
@router.message(StateFilter(RegistrationStates.waiting_for_name))
async def get_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    user_id = message.from_user.id

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (user_id,))
    result = cursor.fetchone()

    if result:
        await message.answer("Вы уже зарегистрированы.")
    else:
        cursor.execute("INSERT INTO users (telegram_id, name) VALUES (?, ?)", (user_id, name))
        conn.commit()
        await message.answer("Спасибо! Теперь отправьте ваш номер телефона.", reply_markup=phone_button)

    conn.close()
    await state.set_state(RegistrationStates.waiting_for_phone)

# Получение номера телефона
@router.message(StateFilter(RegistrationStates.waiting_for_phone), lambda message: message.contact)
async def get_phone(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    phone = message.contact.phone_number

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET phone = ? WHERE telegram_id = ?", (phone, user_id))
    conn.commit()
    conn.close()

    await message.answer("Регистрация завершена! Спасибо!", reply_markup=types.ReplyKeyboardRemove())
    await state.clear()

# Запуск бота
async def main():
    init_db()  # Инициализация базы данных
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
