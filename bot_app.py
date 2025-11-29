import os
import requests
import jsons
import telebot

from Class_ModelResponse import ModelResponse
from db import init_db, get_context, save_context, clear_context
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("TOKEN")
if not API_TOKEN:
    raise RuntimeError("Переменная окружения TOKEN не задана")

bot = telebot.TeleBot(API_TOKEN)


@bot.message_handler(commands=["start"])
def send_welcome(message):
    text = (
        "Привет! Я бот на базе локальной LLM.\n\n"
        "Команды:\n"
        "/start  – помощь\n"
        "/model  – показать модель\n"
        "/clear  – очистить контекст\n\n"
        "Напиши сообщение — я отвечу с учётом контекста."
    )
    bot.reply_to(message, text)


@bot.message_handler(commands=["model"])
def send_model_name(message):
    try:
        response = requests.get("http://localhost:1234/v1/models")
    except requests.RequestException:
        bot.reply_to(message, "Не удалось подключиться к локальному серверу модели.")
        return

    if response.status_code != 200:
        bot.reply_to(message, "Не удалось получить информацию о модели.")
        return

    try:
        model_info = response.json()
        model_name = model_info["data"][0]["id"]
    except (ValueError, KeyError, IndexError):
        bot.reply_to(message, "Ответ сервера моделей в неожиданном формате.")
        return

    bot.reply_to(message, f"Используемая модель: {model_name}")


@bot.message_handler(commands=["clear"])
def clear_user_context(message):
    user_id = message.from_user.id
    clear_context(user_id)
    bot.reply_to(message, "Контекст очищен. Начинаем заново.")


@bot.message_handler(
    func=lambda m: m.text and not m.text.startswith("/"),
    content_types=["text"],
)
def handle_message(message):
    user_id = message.from_user.id
    user_query = message.text

    history = get_context(user_id) or ""

    if history:
        history += "\n"
    history += f"user: {user_query}"

    request = {
        "messages": [
            {
                "role": "user",
                "content": history,
            }
        ]
    }

    try:
        response = requests.post(
            "http://localhost:1234/v1/chat/completions",
            json=request,
        )
    except requests.RequestException:
        bot.reply_to(message, "Не удалось обратиться к локальной LLM (LM Studio).")
        return

    if response.status_code != 200:
        bot.reply_to(message, "Произошла ошибка при обращении к модели.")
        return

    try:
        model_response: ModelResponse = jsons.loads(response.text, ModelResponse)
        answer = model_response.choices[0].message.content
    except Exception:
        bot.reply_to(message, "Ошибка при разборе ответа модели.")
        return

    history += f"\nassistant: {answer}"
    save_context(user_id, history)

    bot.reply_to(message, answer)


def run_bot() -> None:
    init_db()
    bot.polling(none_stop=True)
