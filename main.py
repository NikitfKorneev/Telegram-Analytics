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
from telegram_auth import TelegramAuth
import signal
import sys
from contextlib import asynccontextmanager
import uvicorn
from auth.permissions import require_permission


models.Base.metadata.create_all(bind=engine)

# Flag for tracking application state
is_shutting_down = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown"""
    global telegram_available
    try:
        # Startup
        is_authorized = await telegram_auth.check_auth()
        if not is_authorized:
            print("Telegram авторизация не требуется для просмотра статистики")
            telegram_available = False
        else:
            print("Telegram авторизация успешна")
            telegram_available = True
        yield
    finally:
        # Shutdown
        try:
            await telegram_auth.disconnect()
            print("Telegram client disconnected successfully")
        except Exception as e:
            print(f"Ошибка при отключении от Telegram: {str(e)}")

app = FastAPI(lifespan=lifespan)

# Add session middleware with a secret key
app.add_middleware(SessionMiddleware, secret_key=secrets.token_urlsafe(32))

app.include_router(auth_router, prefix="/auth")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Telegram API
api_id = 24612694
api_hash = '830e613e5101bd49150bf208e29a1e4c'
session_name = 'my_session'

# Initialize TelegramAuth
telegram_auth = TelegramAuth(api_id, api_hash, session_name)

# Регистрируем шрифт для поддержки кириллицы
pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', 'DejaVuSans-Bold.ttf'))

def get_word_frequency(filename, min_word_length=5):
    with open(filename, 'r', encoding='utf-8') as file:
        text = file.read()
        # Извлекаем слова, игнорируя специальные символы и числа
        words = re.findall(r'\b[а-яА-ЯёЁ]{' + str(min_word_length) + ',}\b', text)
        return Counter(words).most_common(20)

async def get_chat_history(chat_name, websocket, start_date=None, end_date=None):
    try:
        if not telegram_auth.client.is_connected():
            await telegram_auth.client.connect()

        await websocket.send_json({"status": "started", "message": "Получаем информацию о чате..."})
        
        chat = await telegram_auth.client.get_entity(chat_name)
        filename = f"chat_history_{chat.id if hasattr(chat, 'id') else chat_name.strip('@')}.txt"

        with open(filename, 'w', encoding='utf-8') as file:
            offset_id = 0
            limit = 100
            total_messages = 0
            total_count = (await telegram_auth.client.get_messages(chat, limit=1)).total

            while True:
                history = await telegram_auth.client(GetHistoryRequest(
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

# Flag for tracking Telegram availability
telegram_available = False

def handle_exit(sig, frame):
    """Handle exit signals"""
    global is_shutting_down
    if not is_shutting_down:
        is_shutting_down = True
        print("\nGracefully shutting down...")
        # Get the current event loop
        loop = asyncio.get_event_loop()
        # Create a task to disconnect Telegram client
        loop.create_task(telegram_auth.disconnect())
        # Stop the event loop
        loop.stop()

# Register signal handlers
signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

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
        # Сохраняем email пользователя в сессии
        request.session['username'] = db_user.email
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
    db: Session = Depends(get_db),
    request: Request = None
):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Сохраняем email пользователя в сессии
    request.session['username'] = user.email
    print(f"Debug - User authenticated: {user.email}")
    print(f"Debug - Session data after login: {request.session}")
    
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

def save_to_history(filename, params, request):
    """Сохраняет информацию о генерации в историю"""
    try:
        print(f"Debug - Starting save_to_history with filename: {filename}")
        print(f"Debug - Parameters: {params}")
        
        history_file = history_dir / 'history.json'
        history = []
        
        # Создаем директорию, если она не существует
        history_dir.mkdir(exist_ok=True)
        print(f"Debug - History directory exists: {history_dir.exists()}")
        
        # Читаем существующую историю, если файл существует
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                print(f"Debug - Loaded existing history with {len(history)} items")
            except json.JSONDecodeError:
                print("Debug - Error reading history file, starting with empty list")
                history = []
        
        # Создаем новую запись без min_word_length
        history_item = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'filename': filename,
            'params': {
                'start_date': params.get('start_date', ''),
                'end_date': params.get('end_date', '')
            }
        }
        print(f"Debug - Created new history item: {history_item}")
        
        # Добавляем новую запись в начало списка
        history.insert(0, history_item)
        
        # Сохраняем обновленную историю
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
            print(f"Debug - History saved successfully to {history_file}")
        
        return history_item['id']
    except Exception as e:
        print(f"Error in save_to_history: {str(e)}")
        return None

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
async def load_history(history_id: str, request: Request):
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
    try:
        data = await request.json()
        print("Debug - update_analysis called with data:", data)
        
        # Получаем текущий файл из сессии
        filename = request.session.get('current_file')
        print(f"Debug - Current file from session: {filename}")
        
        if not filename:
            raise HTTPException(status_code=404, detail="Файл не найден")
        
        # Сохраняем новые параметры в сессию (без min_word_length)
        request.session['analysis_params'] = {
            'start_date': data.get('start_date'),
            'end_date': data.get('end_date')
        }
        print(f"Debug - Updated session params: {request.session['analysis_params']}")
        
        # Сохраняем в историю
        history_id = save_to_history(filename, request.session['analysis_params'], request)
        print(f"Debug - History saved with ID: {history_id}")
        
        return RedirectResponse(url=f"/get_history?filename={filename}")
    except Exception as e:
        print(f"Error in update_analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_history")
async def get_history(request: Request, filename: str):
    try:
        print(f"Debug - get_history called with filename: {filename}")
        
        if not os.path.exists(filename):
            print(f"Debug - File not found: {filename}")
            return RedirectResponse(url="/")

        # Получаем параметры из сессии или используем значения по умолчанию
        params = request.session.get('analysis_params', {})
        
        # Сохраняем имя файла в сессии
        request.session['current_file'] = filename
        print(f"Debug - Saved filename to session: {filename}")
        
        # Сохраняем в историю при первом открытии файла
        if not params:
            params = {
                'start_date': '',
                'end_date': ''
            }
            history_id = save_to_history(filename, params, request)
            print(f"Debug - Initial history saved with ID: {history_id}")
        
        word_count = count_words_in_file(filename)
        plots = create_plots(filename)

        # Создаем словарь с графиками
        plot_dict = {
            "request": request,
            "word_count": word_count,
            "telegram_available": telegram_available
        }
        
        # Добавляем все графики в словарь
        for i, plot in enumerate(plots):
            plot_dict[f"plot{i}"] = plot

        # Проверяем, что у нас есть все 10 графиков
        for i in range(10):
            if f"plot{i}" not in plot_dict:
                plot_dict[f"plot{i}"] = ""

        return templates.TemplateResponse("stats.html", plot_dict)
    except Exception as e:
        print(f"Error in get_history: {str(e)}")
        return RedirectResponse(url="/")

@app.get("/protected-route")
async def protected_route(current_user: User = Depends(get_current_active_user)):
    return {"message": "This is a protected route", "user": current_user.username}

@app.get("/download_pdf")
async def download_pdf(request: Request, history_id: str = None):
    try:
        filename = None
        params = None
        
        if history_id:
            # Если передан ID истории, загружаем параметры из истории
            history_file = history_dir / 'history.json'
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    history_item = next((item for item in history if item['id'] == history_id), None)
                    if history_item:
                        filename = history_item['filename']
                        params = history_item['params']
        else:
            # Иначе используем текущий файл из сессии
            filename = request.session.get('current_file')
            params = request.session.get('analysis_params', {})

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

@app.get("/telegram-auth")
async def telegram_auth_page(request: Request):
    """Render Telegram authentication page"""
    return templates.TemplateResponse("telegram_auth.html", {"request": request})

@app.get("/telegram/qr-code")
async def get_qr_code():
    """Generate QR code for Telegram login"""
    result = await telegram_auth.generate_qr_code()
    return JSONResponse(result)

@app.get("/telegram/verify-qr/{token}")
async def verify_qr_code(token: str):
    """Verify QR code login"""
    result = await telegram_auth.verify_qr_code(token)
    return JSONResponse(result)

@app.post("/telegram/phone-auth")
async def phone_auth(request: Request):
    """Handle phone number authentication"""
    data = await request.json()
    phone_number = data.get("phone_number")
    code = data.get("code")
    password = data.get("password")
    
    result = await telegram_auth.phone_auth(phone_number, code, password)
    return JSONResponse(result)

@app.get("/telegram/check-auth")
async def check_telegram_auth():
    """Check if user is authorized in Telegram"""
    is_authorized = await telegram_auth.check_auth()
    return JSONResponse({"authorized": is_authorized})

@app.post("/telegram/complete-qr-auth")
async def complete_qr_auth(request: Request):
    """Complete QR code authentication with password"""
    data = await request.json()
    password = data.get("password")
    
    if not password:
        return JSONResponse({
            "status": "error",
            "message": "Пароль не указан"
        })
    
    result = await telegram_auth.complete_qr_auth(password)
    return JSONResponse(result)

@app.get("/admin", response_class=HTMLResponse)
@require_permission("manage_users")
async def admin_panel(request: Request, current_user: User = Depends(get_current_active_user)):
    return templates.TemplateResponse("admin.html", {"request": request})

if __name__ == "__main__":
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=8000,
        loop="asyncio",
        log_level="info"
    )
    server = uvicorn.Server(config)
    server.run()