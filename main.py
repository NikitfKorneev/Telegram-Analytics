from fastapi import FastAPI, WebSocket, Request, Depends, Form, HTTPException, status
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import GetHistoryRequest
import asyncio
import json
import os
from datetime import datetime
from auth.router import router as auth_router
from auth.dependencies import get_current_active_user
from auth.schemas import User, UserCreate
from auth import crud, utils
from auth.database import get_db
from sqlalchemy.orm import Session
from utils import count_words_in_file, create_plots
from auth import models
from auth.database import engine

models.Base.metadata.create_all(bind=engine)
app = FastAPI()
app.include_router(auth_router, prefix="/auth")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Telegram API
api_id = 24612694
api_hash = '830e613e5101bd49150bf208e29a1e4c'
phone_number = '89160071580'
session_name = 'my_session'
client = TelegramClient(session_name, api_id, api_hash)

async def start_telegram_client():
    try:
        await client.connect()
        if not await client.is_user_authorized():
            print("Отправка кода подтверждения...")
            await client.send_code_request(phone_number)
            code = input("Введите код из Telegram: ")
            await client.sign_in(phone_number, code)
        return True
    except SessionPasswordNeededError:
        password = input("Введите пароль двухфакторной аутентификации: ")
        await client.sign_in(password=password)
        return True
    except Exception as e:
        print(f"Ошибка авторизации: {str(e)}")
        return False

async def get_chat_history(chat_name, websocket, start_date=None, end_date=None):
    try:
        if not client.is_connected():
            await client.connect()

        await websocket.send_json({"status": "started", "message": "Получаем информацию о чате..."})
        
        chat = await client.get_entity(chat_name)
        filename = f"chat_history_{chat.id if hasattr(chat, 'id') else chat_name.strip('@')}.txt"

        with open(filename, 'w', encoding='utf-8') as file:
            offset_id = 0
            limit = 100
            total_messages = 0
            total_count = (await client.get_messages(chat, limit=1)).total

            while True:
                history = await client(GetHistoryRequest(
                    peer=chat,
                    offset_id=offset_id,
                    offset_date=None,
                    add_offset=0,
                    limit=limit,
                    max_id=0,
                    min_id=0,
                    hash=0
                ))

                if not history.messages:
                    break

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

                progress = (total_messages / total_count) * 100 if total_count else total_messages
                await websocket.send_json({
                    "progress": progress,
                    "status": "loading",
                    "filename": filename,
                    "loaded": total_messages,
                    "total": total_count
                })

                offset_id = history.messages[-1].id
                await asyncio.sleep(0.1)

            await websocket.send_json({
                "progress": 100,
                "status": "completed",
                "filename": filename,
                "message": "Загрузка завершена"
            })

    except Exception as e:
        await websocket.send_json({"status": "error", "message": str(e)})

@app.on_event("startup")
async def startup_event():
    if not await start_telegram_client():
        print("Не удалось авторизоваться в Telegram. Некоторые функции могут быть недоступны")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("welcome.html", {"request": request})

@app.post("/auth/register")
async def register_user(
    request: Request,
    name: str = Form(...),
    username: str = Form(...),
    email: str = Form(None),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    if password != confirm_password:
        return templates.TemplateResponse(
            "welcome.html",
            {"request": request, "error": "Пароли не совпадают"},
            status_code=400
        )
    
    user = UserCreate(
        username=username,
        name=name,
        email=email,
        password=password
    )
    
    try:
        db_user = crud.create_user(db, user)
        return RedirectResponse(url="/", status_code=303)
    except Exception as e:
        return templates.TemplateResponse(
            "welcome.html",
            {"request": request, "error": str(e)},
            status_code=400
        )

@app.post("/auth/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = utils.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/welcome")
async def welcome(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        
        if "chat_name" not in data:
            await websocket.send_json({"status": "error", "message": "Не указано имя чата"})
            return

        start_date = None
        end_date = None
        try:
            if data.get("start_date"):
                start_date = datetime.strptime(data["start_date"], "%Y-%m-%d").date()
            if data.get("end_date"):
                end_date = datetime.strptime(data["end_date"], "%Y-%m-%d").date()
        except ValueError as e:
            await websocket.send_json({"status": "error", "message": f"Неверный формат даты: {str(e)}"})
            return

        await get_chat_history(data["chat_name"], websocket, start_date, end_date)
        
    except json.JSONDecodeError:
        await websocket.send_json({"status": "error", "message": "Неверный формат данных"})
    except Exception as e:
        await websocket.send_json({"status": "error", "message": f"Ошибка: {str(e)}"})
    finally:
        await websocket.close()

@app.get("/get_history")
async def get_history(request: Request, filename: str, min_word_length: int = 5):
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

@app.get("/protected-route")
async def protected_route(current_user: User = Depends(get_current_active_user)):
    return {"message": "This is a protected route", "user": current_user.username}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)