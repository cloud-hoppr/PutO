import os
import asyncio
import json
import time
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import keyboard
from dotenv import load_dotenv
from prompt import (
    generate_task_plan,
    get_current_step,
    complete_current_step
)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("ОШИБКА: Проверь BOT_TOKEN в файле .env!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Структура: { user_id: {"xp": 0, "mood": 50, "steps": ["шаг 1", "шаг 2"]} }
users_data = {}

def get_user(user_id: int) -> dict:
    if user_id not in users_data:
        users_data[user_id] = {"xp": 0, "mood": 50, "steps": []}
    return users_data[user_id]

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    get_user(message.from_user.id)
    github_url = "https://cloud-hoppr.github.io/PutO/"
    mini_app_url = f"{github_url}?v={int(time.time())}"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🦊 Открыть Напарника", web_app=WebAppInfo(url=mini_app_url))]
    ])

    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n"
        "Я готов раздробить любую сложную задачу на крошечные шаги.\n"
        "Жми кнопку ниже, чтобы начать!",
        reply_markup=keyboard
    )


@dp.message(lambda message: message.web_app_data)
async def handle_web_app_data(message: types.Message):
    user = get_user(message.from_user.id)
    data = json.loads(message.web_app_data.data)

    if data.get("action") == "split_task":
        task_title = data.get("task")
        #await message.answer(f"🤔 Напарник разбивает задачу «{task_title}»...")

        # try:
        #     steps = await generate_task_plan(task_title)
        # 
        #     user["steps"] = steps
        #     user["current_index"] = 0
        #
        #     step = get_current_step(user["steps"], user["current_index"])



async def main():
    print("🤖 Запуск бота...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

