from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from handlers import websocket_endpoint, get_history, start_telegram_client

app = FastAPI()

# Подключение статических файлов (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключение шаблонов
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
async def startup_event():
    """Запускаем Telegram-клиент при старте сервера"""
    await start_telegram_client()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# WebSocket для получения истории чатов
app.websocket("/ws")(websocket_endpoint)

# Отображение результатов анализа
app.get("/get_history", response_class=HTMLResponse)(get_history)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
