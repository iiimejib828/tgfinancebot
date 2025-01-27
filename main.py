import asyncio
import random
from datetime import datetime

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import TOKEN, API_KEY
import sqlite3
import aiohttp
import logging
import time

bot = Bot(token=TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

button_registr = KeyboardButton(text="Регистрация в телеграм боте")
button_exchange_rates = KeyboardButton(text="Курс валют")
button_tips = KeyboardButton(text="Советы по экономии")
button_finances = KeyboardButton(text="Внести расходы")
button_expences = KeyboardButton(text="Посмотреть расходы")

keyboards = ReplyKeyboardMarkup(keyboard=[
    [button_registr, button_exchange_rates],
    [button_tips, button_finances, button_expences]
    ], resize_keyboard=True)

conn = sqlite3.connect('user.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    telegram_id INTEGER UNIQUE,
    name TEXT
    )
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS expences (
    id INTEGER PRIMARY KEY,
    telegram_id INTEGER,
    date INTEGER,
    category1 TEXT,
    category2 TEXT,
    category3 TEXT,
    expenses1 REAL,
    expenses2 REAL,
    expenses3 REAL
    )
''')

conn.commit()

class FinancesForm(StatesGroup):
    category1 = State()
    expenses1 = State()
    category2 = State()
    expenses2 = State()
    category3 = State()
    expenses3 = State()


@dp.message(Command('start'))
async def send_start(message: Message):
    await message.answer("Привет! Я ваш личный финансовый помощник. Выберите одну из опций в меню:", reply_markup=keyboards)

@dp.message(F.text == "Регистрация в телеграм боте")
async def registration(message: Message):
    telegram_id = message.from_user.id
    name = message.from_user.full_name
    cursor.execute('''SELECT * FROM users WHERE telegram_id = ?''', (telegram_id,))
    user = cursor.fetchone()
    if user:
        await message.answer("Вы уже зарегистрированы!")
    else:
        cursor.execute('''INSERT INTO users (telegram_id, name) VALUES (?, ?)''', (telegram_id, name))
        conn.commit()
        await message.answer("Вы успешно зарегистрированы!")

@dp.message(F.text == "Курс валют")
async def exchange_rates(message: Message):
    url = "https://v6.exchangerate-api.com/v6/" + API_KEY + "/latest/USD"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url) as response:
                if response.status == 200:
                    data = await response.json()  # Получаем JSON-ответ
                    usd_to_rub = data['conversion_rates']['RUB']
                    eur_to_usd = data['conversion_rates']['EUR']

                    euro_to_rub = eur_to_usd * usd_to_rub

                    await message.answer(f"1 USD - {usd_to_rub:.2f}  RUB\n"
                                         f"1 EUR - {euro_to_rub:.2f}  RUB")
                else:
                    await message.answer("Не удалось получить данные о курсах валют!")
    except:
        await message.answer("Произошла ошибка")

@dp.message(F.text == "Советы по экономии")
async def send_tips(message: Message):
    tips = [
        "Совет 1: Планируйте покупки заранее. Составляйте список необходимых вещей, чтобы избежать импульсивных трат.",
        "Совет 2: Используйте скидки и кэшбэк. Следите за акциями и распродажами, чтобы покупать нужные товары дешевле.",
        "Совет 3: Готовьте дома. Еда на вынос и походы в кафе обходятся дороже, чем приготовление дома.",
        "Совет 4: Откладывайте фиксированную сумму. Ежемесячно переводите часть дохода на сберегательный счёт.",
        "Совет 5: Выключайте ненужную электронику. Экономьте электроэнергию, отключая приборы из розеток, когда они не используются.",
        "Совет 6: Сравнивайте цены. Перед покупкой проверяйте стоимость товара в разных магазинах.",
        "Совет 7: Откажитесь от ненужных подписок. Регулярно проверяйте, какими сервисами вы пользуетесь, и отменяйте те, которые не нужны.",
        "Совет 8: Используйте общественный транспорт. Это дешевле, чем содержание автомобиля.",
        "Совет 9: Ремонтируйте, а не заменяйте. Старайтесь чинить вещи, вместо того чтобы покупать новые.",
        "Совет 10: Устанавливайте цели на сбережения. Это поможет дисциплинировать расходы и мотивирует вас копить деньги."
    ]
    tip = random.choice(tips)
    await message.answer(tip)

@dp.message(F.text == "Внести расходы")
async def finances(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    name = message.from_user.full_name
    cursor.execute('''SELECT * FROM users WHERE telegram_id = ?''', (telegram_id,))
    user = cursor.fetchone()
    if user:
        await state.set_state(FinancesForm.category1)
        await message.reply("Введите первую категорию расходов:")
    else:
        await message.answer("Вы ещё не зарегистрированы!")

@dp.message(FinancesForm.category1)
async def finances(message: Message, state: FSMContext):
    await state.update_data(category1 = message.text)
    await state.set_state(FinancesForm.expenses1)
    await message.reply("Введите расходы для категории 1:")

@dp.message(FinancesForm.expenses1)
async def finances(message: Message, state: FSMContext):
    await state.update_data(expenses1 = float(message.text))
    await state.set_state(FinancesForm.category2)
    await message.reply("Введите вторую категорию расходов:")

@dp.message(FinancesForm.category2)
async def finances(message: Message, state: FSMContext):
    await state.update_data(category2 = message.text)
    await state.set_state(FinancesForm.expenses2)
    await message.reply("Введите расходы для категории 2:")

@dp.message(FinancesForm.expenses2)
async def finances(message: Message, state: FSMContext):
    await state.update_data(expenses2 = float(message.text))
    await state.set_state(FinancesForm.category3)
    await message.reply("Введите третью категорию расходов:")

@dp.message(FinancesForm.category3)
async def finances(message: Message, state: FSMContext):
    await state.update_data(category3 = message.text)
    await state.set_state(FinancesForm.expenses3)
    await message.reply("Введите расходы для категории 3:")

@dp.message(FinancesForm.expenses3)
async def finances(message: Message, state: FSMContext):
    data = await state.get_data()
    telegarm_id = message.from_user.id
    cursor.execute('''INSERT INTO expences (telegram_id, date, category1, expenses1, category2, expenses2,
    category3, expenses3) VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
    (telegarm_id, int(time.time()), data['category1'], float(data['expenses1']), data['category2'], float(data['expenses2']), data['category3'], float(message.text) ))
    conn.commit()
    await state.clear()

    await message.answer("Категории и расходы сохранены!")

@dp.message(F.text == "Посмотреть расходы")
async def expences(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    cursor.execute('''SELECT * FROM users WHERE telegram_id = ?''', (telegram_id,))
    user = cursor.fetchone()
    if user:
        cursor.execute('''SELECT * FROM expences WHERE telegram_id = ?''', (telegram_id,))
        data = cursor.fetchall()
        if data:
            # Заголовок таблицы
            expences_list = "Ваши расходы:\n```\n"
            expences_list += f"{'ID':<5}{'Дата':<20}{'Категория 1':<15}{'Сумма 1':<10}{'Категория 2':<15}{'Сумма 2':<10}{'Категория 3':<15}{'Сумма 3':<10}\n"
            expences_list += "-" * 100 + "\n"

            # Формируем строки таблицы
            for record in data:
                date = datetime.fromtimestamp(record[2]).strftime('%d.%m.%Y %H:%M:%S')
                expences_list += f"{record[0]:<5}{date:<20}{record[3]:<15}{record[6]:<10.2f}{record[4]:<15}{record[7]:<10.2f}{record[5]:<15}{record[8]:<10.2f}\n"

            expences_list += "```"  # Закрываем блок моноширинного текста
        else:
            expences_list = "Нет данных о расходах."

        await message.answer(expences_list, parse_mode="Markdown")

    else:
        await message.answer("Вы ещё не зарегистрированы!")


async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())