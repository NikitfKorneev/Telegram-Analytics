from fastapi import FastAPI, WebSocket, Request, Depends, Form, HTTPException, status
from fastapi.responses import RedirectResponse, HTMLResponse, FileResponse, Response, JSONResponse
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
from pathlib import Path
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
import base64
from starlette.middleware.sessions import SessionMiddleware
import secrets
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from collections import Counter
import re
from pdf_generator import create_pdf
import uuid
from pydantic import BaseModel

models.Base.metadata.create_all(bind=engine)
app = FastAPI()

# Add session middleware with a secret key
app.add_middleware(SessionMiddleware, secret_key=secrets.token_urlsafe(32))

app.include_router(auth_router, prefix="/auth")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Telegram API
api_id = 24612694
api_hash = '830e613e5101bd49150bf208e29a1e4c'
session_name = 'my_session'
client = TelegramClient(session_name, api_id, api_hash)

# Регистрируем шрифт для поддержки кириллицы
pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', 'DejaVuSans-Bold.ttf'))

def get_word_frequency(filename, min_word_length=5):
    with open(filename, 'r', encoding='utf-8') as file:
        text = file.read()
        # Извлекаем слова, игнорируя специальные символы и числа
        words = re.findall(r'\b[а-яА-ЯёЁ]{' + str(min_word_length) + ',}\b', text)
        return Counter(words).most_common(20)

async def start_telegram_client(phone_number: str, code: str = None, password: str = None):
    try:
        await client.connect()
        if not await client.is_user_authorized():
            if not code:
                try:
                    await client.send_code_request(phone_number)
                    print(f"Код подтверждения отправлен на номер {phone_number}")  # Для отладки
                    return {"status": "code_required", "message": "Код подтверждения отправлен"}
                except Exception as e:
                    print(f"Ошибка при отправке кода: {str(e)}")  # Для отладки
                    return {"status": "error", "message": f"Ошибка при отправке кода: {str(e)}"}
            try:
                await client.sign_in(phone_number, code)
            except SessionPasswordNeededError:
                if not password:
                    return {"status": "password_required", "message": "Требуется пароль двухфакторной аутентификации"}
                await client.sign_in(password=password)
        return {"status": "success", "message": "Авторизация успешна"}
    except Exception as e:
        print(f"Ошибка авторизации: {str(e)}")  # Для отладки
        return {"status": "error", "message": str(e)}

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

# Добавляем флаг для отслеживания состояния Telegram
telegram_available = False

@app.on_event("startup")
async def startup_event():
    global telegram_available
    try:
        if not client.is_connected():
            await client.connect()
            
        if not await client.is_user_authorized():
            print("Telegram авторизация не требуется для просмотра статистики")
            telegram_available = False
        else:
            print("Telegram авторизация успешна")
            telegram_available = True
    except Exception as e:
        print(f"Ошибка при подключении к Telegram: {str(e)}")
        telegram_available = False

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("welcome.html", {"request": request})

@app.get("/tutorial", response_class=HTMLResponse)
async def tutorial(request: Request):
    return templates.TemplateResponse("tutorial.html", {"request": request})

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

# Создаем директорию для хранения истории
history_dir = Path('history')
history_dir.mkdir(exist_ok=True)

def save_to_history(filename, params):
    """Сохраняет информацию о генерации в историю"""
    history_file = history_dir / 'history.json'
    history = []
    
    if history_file.exists():
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
    
    history_item = {
        'id': str(uuid.uuid4()),
        'timestamp': datetime.now().isoformat(),
        'filename': filename,
        'params': params
    }
    
    history.append(history_item)
    
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    
    return history_item['id']

@app.get("/get_history_list")
async def get_history_list():
    """Возвращает список истории генерации"""
    history_file = history_dir / 'history.json'
    if not history_file.exists():
        return JSONResponse([])
    
    with open(history_file, 'r', encoding='utf-8') as f:
        history = json.load(f)
    
    return JSONResponse(history)

@app.get("/load_history/{history_id}")
async def load_history(history_id: str):
    """Загружает конкретный элемент истории"""
    history_file = history_dir / 'history.json'
    if not history_file.exists():
        raise HTTPException(status_code=404, detail="История не найдена")
    
    with open(history_file, 'r', encoding='utf-8') as f:
        history = json.load(f)
    
    history_item = next((item for item in history if item['id'] == history_id), None)
    if not history_item:
        raise HTTPException(status_code=404, detail="Элемент истории не найден")
    
    # Сохраняем параметры в сессию
    request.session['current_file'] = history_item['filename']
    request.session['analysis_params'] = history_item['params']
    
    return RedirectResponse(url=f"/get_history?filename={history_item['filename']}")

@app.post("/update_analysis")
async def update_analysis(request: Request):
    """Обновляет параметры анализа"""
    data = await request.json()
    
    # Получаем текущий файл из сессии
    filename = request.session.get('current_file')
    if not filename:
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    # Сохраняем новые параметры в сессию
    request.session['analysis_params'] = {
        'min_word_length': data.get('min_word_length', 5),
        'start_date': data.get('start_date'),
        'end_date': data.get('end_date')
    }
    
    # Сохраняем в историю
    save_to_history(filename, request.session['analysis_params'])
    
    return RedirectResponse(url=f"/get_history?filename={filename}")

@app.get("/get_history")
async def get_history(request: Request, filename: str):
    if not os.path.exists(filename):
        return RedirectResponse(url="/")

    try:
        # Получаем параметры из сессии или используем значения по умолчанию
        params = request.session.get('analysis_params', {})
        min_word_length = params.get('min_word_length', 5)
        
        # Сохраняем имя файла в сессии
        request.session['current_file'] = filename
        
        word_count = count_words_in_file(filename)
        plots = create_plots(filename, min_word_length)

        return templates.TemplateResponse("stats.html", {
            "request": request,
            "word_count": word_count,
            "plot0": plots[0] if len(plots) > 0 else '',
            "plot1": plots[1] if len(plots) > 1 else '',
            "plot2": plots[2] if len(plots) > 2 else '',
            "plot3": plots[3] if len(plots) > 3 else '',
            "plot4": plots[4] if len(plots) > 4 else '',
            "telegram_available": telegram_available
        })
    except Exception as e:
        print(f"Error in get_history: {str(e)}")
        return RedirectResponse(url="/")

@app.get("/protected-route")
async def protected_route(current_user: User = Depends(get_current_active_user)):
    return {"message": "This is a protected route", "user": current_user.username}

@app.get("/download_pdf")
async def download_pdf(request: Request):
    try:
        # Получаем имя файла из сессии
        filename = request.session.get('current_file')
        if not filename:
            raise HTTPException(status_code=404, detail="Файл не найден")

        # Проверяем существование файла
        if not os.path.exists(filename):
            raise HTTPException(status_code=404, detail=f"Файл {filename} не найден")

        # Получаем количество слов и графики
        word_count = count_words_in_file(filename)
        plots = create_plots(filename)

        # Создаем PDF
        pdf_path, pdf_filename = create_pdf(filename, plots, word_count)

        # Отправляем файл
        return FileResponse(
            path=pdf_path,
            filename=pdf_filename,
            media_type='application/pdf'
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

class PasswordChange(BaseModel):
    email: str
    current_password: str
    new_password: str

@app.post("/change_password")
async def change_password(
    password_data: PasswordChange,
    db: Session = Depends(get_db)
):
    """Изменение пароля пользователя"""
    # Находим пользователя по email
    user = crud.get_user_by_email(db, password_data.email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Пользователь с таким email не найден"
        )
    
    # Проверяем текущий пароль
    if not utils.verify_password(password_data.current_password, user.hashed_password):
        raise HTTPException(
            status_code=400,
            detail="Неверный текущий пароль"
        )
    
    # Хешируем новый пароль
    hashed_password = utils.get_password_hash(password_data.new_password)
    
    # Обновляем пароль в базе данных
    user.hashed_password = hashed_password
    db.commit()
    
    return {"message": "Пароль успешно изменен"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)