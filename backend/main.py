import os
import asyncio
import time
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from aiohttp import web
import json
from urllib.parse import parse_qs
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

users = {}

def get_user_id(request):
    init_data = request.headers.get("X-Telegram-Init-Data", "")

    try:
        data = parse_qs(init_data)
        user = json.loads(data["user"][0])
        return str(user["id"])
    except (KeyError, IndexError, ValueError):
        return "local"

HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", "10000"))


async def health(request):
    return web.json_response({
        "status": "ok",
        "message": "Backend работает!"
    })

async def create_task(request):
    user_id = get_user_id(request)

    try:
        data = await request.json()
        task = data.get("task", "").strip()

        if not task:
            return web.json_response(
                {"error": "Напиши задачу!"},
                status=400
            )

        if len(task) > 500:
            return web.json_response(
                {"error": "Слишком длинная задача."},
                status=400
            )

        print(f"📝 Новая задача: {task}")

        steps = await generate_task_plan(task)

        users[user_id] = {
            "steps": steps,
            "current_index": 0,
            "xp": users.get(user_id, {}).get("xp", 0)
        }

        return web.json_response({
            "steps": steps,
            "current_step": steps[0],
            "current_index": 0,
            "total_steps": len(steps),
            "profile": {
                "xp": users[user_id]["xp"],
                "mood": 50
            }
        })

    except Exception as error:
        print(f"❌ Ошибка создания задачи: {error}")

        return web.json_response(
            {"error": "Не удалось создать план. Попробуй ещё раз."},
            status=500
        )

async def complete_step(request):
    user_id = get_user_id(request)
    user = users.get(user_id)

    if not user or not user["steps"]:
        return web.json_response(
            {"error": "Нет активной задачи."},
            status=400
        )

    result = complete_current_step(
        user["steps"],
        user["current_index"]
    )

    user["current_index"] = result["next_index"]
    user["xp"] += 10

    return web.json_response({
        "completed": result["completed"],
        "current_step": result["next_step"],
        "current_index": user["current_index"],
        "total_steps": len(user["steps"]),
        "profile": {
            "xp": user["xp"],
            "mood": 50
        }
    })

@web.middleware
async def cors_middleware(request, handler):
    if request.method == "OPTIONS":
        response = web.Response(status=204)
    else:
        response = await handler(request)

    origin = request.headers.get("Origin")

    if origin == "https://cloud-hoppr.github.io":
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Headers"] = (
            "Content-Type, X-Telegram-Init-Data"
        )
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"

    return response

async def start_http_server():
    app = web.Application(middlewares=[cors_middleware])

    app.router.add_get("/health", health)
    app.router.add_post("/api/tasks", create_task)
    app.router.add_post("/api/steps/complete", complete_step)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, HOST, PORT)
    await site.start()

    print(f"🌐 HTTP-сервер запущен на порту {PORT}")

    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
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

async def main():
    print("🤖 Запуск бота и HTTP-сервера...")

    await asyncio.gather(
        dp.start_polling(bot),
        start_http_server()
    )


if __name__ == "__main__":
    asyncio.run(main())

