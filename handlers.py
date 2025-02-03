from fastapi import WebSocket, Request
from fastapi.responses import RedirectResponse
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import GetHistoryRequest
import asyncio
import json
import os
from datetime import datetime
from utils import create_plots, count_words_in_file
from fastapi.templating import Jinja2Templates

# Telegram API
api_id = 'api_id'  
api_hash = 'api_hash'
phone_number = 'phone_number'  
session_name = 'my_session'

client = TelegramClient(session_name, api_id, api_hash)
templates = Jinja2Templates(directory="templates")

async def start_telegram_client():
    """Запускает Telegram-клиент при старте сервера"""
    await client.connect()
    if not await client.is_user_authorized():
        await client.send_code_request(phone_number)
        try:
            code = input("Введите код из Telegram: ")
            await client.sign_in(phone_number, code)
        except SessionPasswordNeededError:
            password = input("Введите пароль двухфакторной аутентификации: ")
            await client.sign_in(password=password)

async def get_chat_history(chat_name, websocket, start_date=None, end_date=None):
    """Загружает историю чата и передает прогресс в WebSocket."""
    try:
        if not client.is_connected():
            await client.connect()

        chat = await client.get_entity(chat_name)
        filename = f"chat_history_{chat.id if hasattr(chat, 'id') else chat_name.strip('@')}.txt"

        with open(filename, 'w', encoding='utf-8') as file:
            offset_id = 0
            limit = 100  # Сколько сообщений загружать за раз
            total_messages = 0
            total_count = (await client.get_messages(chat, limit=1)).total  # Получаем общее число сообщений

            while True:
                history = await client(GetHistoryRequest(
                    peer=chat,
                    offset_id=offset_id,
                    offset_date=None,  # Эти параметры обязательны, но мы их не используем
                    add_offset=0,
                    limit=limit,
                    max_id=0,
                    min_id=0,
                    hash=0
                ))

                if not history.messages:
                    break  # Если сообщений больше нет, выходим

                # Фильтруем сообщения по дате
                filtered_messages = [
                    msg for msg in history.messages
                    if (not start_date or msg.date.date() >= start_date) and 
                       (not end_date or msg.date.date() <= end_date)
                ]

                for message in filtered_messages:
                    sender = message.sender_id if message.sender_id else "Unknown"
                    text = message.message.replace("\n", " ") if message.message else " "
                    file.write(f"{message.date} - {sender}: {text}\n")
                    total_messages += 1

                # Обновляем прогресс
                progress = (total_messages / total_count) * 100 if total_count else total_messages
                await websocket.send_json({"progress": progress, "status": "loading", "filename": filename})

                # Смещаем offset для следующего запроса
                offset_id = history.messages[-1].id
                await asyncio.sleep(0.1)

            # Завершаем загрузку
            await websocket.send_json({"progress": 100, "status": "completed", "filename": filename})

    except Exception as e:
        await websocket.send_json({"status": "error", "message": str(e)})

async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    data = json.loads(await websocket.receive_text())

    chat_name = data["chat_name"]
    start_date = datetime.strptime(data["start_date"], "%Y-%m-%d").date() if data["start_date"] else None
    end_date = datetime.strptime(data["end_date"], "%Y-%m-%d").date() if data["end_date"] else None

    await get_chat_history(chat_name, websocket, start_date, end_date)

async def get_history(request: Request, filename: str, min_word_length: int = 5):
    """Генерирует анализ данных и отображает его в шаблоне stats.html."""
    if not os.path.exists(filename):
        return RedirectResponse(url="/")

    try:
        word_count = count_words_in_file(filename)
        plots = create_plots(filename, min_word_length)

        return templates.TemplateResponse("stats.html", {
            "request": request,
            "word_count": word_count,
            "plot0": plots[0] if len(plots) > 0 else '',
            "plot1": plots[1] if len(plots) > 1 else '',
            "plot2": plots[2] if len(plots) > 2 else '',
            "plot3": plots[3] if len(plots) > 3 else '',
            "plot4": plots[4] if len(plots) > 4 else ''
        })

    except Exception as e:
        print(f"Error in get_history: {str(e)}")
        return RedirectResponse(url="/")
