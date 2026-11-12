import os
import json
from dotenv import load_dotenv
from groq import AsyncGroq

load_dotenv()

client = AsyncGroq(
    api_key=os.getenv("GROQ_API_KEY")
)

MODEL = "openai/gpt-oss-20b"

async def generate_task_plan(task: str) -> list:
    if not task or not task.strip():
        raise ValueError("Задача не может быть пустой")

    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": """
Ты — ИИ-напарник по борьбе с прокрастинацией.

Твоя задача — превращать большие задачи
в последовательность маленьких конкретных действий.

Правила:
1. Создай от 5 до 10 шагов.
2. Первые 2-3 шага должны занимать 1-3 минуты.
3. Последующие шаги могут занимать 5-15 минут.
4. Каждый шаг содержит только одно действие.
5. Используй простые и понятные формулировки.
6. Не начинай с трудных действий.
7. Соблюдай логическую последовательность.
8. Пиши ВСЁ содержимое на русском языке: названия шагов и любые текстовые значения.
9. Не используй английские фразы, если это не официальное название, термин или имя собственное.

Верни результат в формате JSON.
Не добавляй пояснений за пределами JSON.
"""
            },
            {
                "role": "user",
                "content": (
                    f"Разбей следующую задачу на микрошаги: {task}\n"
                    "Верни JSON с полем steps."
                )
            }
        ],

        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "task_plan",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "steps": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {
                                        "type": "string"
                                    },
                                    "minutes": {
                                        "type": "integer"
                                    }
                                },
                                "required": [
                                    "title",
                                    "minutes"
                                ],
                                "additionalProperties": False
                            }
                        }
                    },
                    "required": ["steps"],
                    "additionalProperties": False
                }
            }
        }
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError("ИИ вернул пустой ответ")

    result = json.loads(content)
    steps = result["steps"]

    if not 5 <= len(steps) <= 10:
        raise ValueError("ИИ создал неправильное количество шагов")

    for step in steps:
        if not step["title"].strip():
            raise ValueError("Обнаружен пустой шаг")

        if step["minutes"] < 1:
            raise ValueError("Некорректное время выполнения")

    return steps



def get_current_step(steps: list, current_index: int):
    if current_index < 0 or current_index >= len(steps):
        return None

    return steps[current_index]


def complete_current_step(steps: list, current_index: int):
    next_index = current_index + 1

    if next_index >= len(steps):
        return {
            "completed": True,
            "next_index": next_index,
            "next_step": None
        }

    return {
        "completed": False,
        "next_index": next_index,
        "next_step": get_current_step(steps, next_index)
    }
