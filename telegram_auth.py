from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, AuthTokenExpiredError
from telethon.tl.functions.auth import ExportLoginTokenRequest
from telethon.tl.functions.auth import ImportLoginTokenRequest
import qrcode
from io import BytesIO
import base64
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

class TelegramAuth:
    def __init__(self, api_id: int, api_hash: str, session_name: str = 'my_session'):
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_name = session_name
        self.client = TelegramClient(session_name, api_id, api_hash)
        self._auth_state = {}
        self._is_connected = False
        self._disconnect_lock = asyncio.Lock()
        self._token_expiry = None

    async def connect(self):
        """Connect to Telegram"""
        if not self._is_connected:
            try:
                await self.client.connect()
                self._is_connected = True
            except Exception as e:
                self._is_connected = False
                raise e

    async def disconnect(self):
        """Disconnect from Telegram"""
        async with self._disconnect_lock:
            if self._is_connected:
                try:
                    # Cancel any pending operations
                    for task in asyncio.all_tasks():
                        if not task.done() and task != asyncio.current_task():
                            task.cancel()
                    
                    # Wait for a short time to allow tasks to cancel
                    await asyncio.sleep(0.1)
                    
                    # Disconnect the client
                    await self.client.disconnect()
                    self._is_connected = False
                    print("Successfully disconnected from Telegram")
                except Exception as e:
                    print(f"Error during disconnect: {str(e)}")
                    raise
                finally:
                    self._is_connected = False

    def _is_token_expired(self) -> bool:
        """Check if the current token is expired"""
        if not self._token_expiry:
            return True
        return datetime.now() > self._token_expiry

    async def generate_qr_code(self) -> Dict[str, Any]:
        """Generate QR code for Telegram login"""
        try:
            await self.connect()
            
            # Request QR code login
            result = await self.client(ExportLoginTokenRequest(
                api_id=self.api_id,
                api_hash=self.api_hash,
                except_ids=[]
            ))
            
            # Store token and set expiry time (5 minutes from now)
            token = result.token
            self._auth_state['token'] = token
            self._token_expiry = datetime.now() + timedelta(minutes=5)
            
            # Generate QR code URL
            qr_url = f"tg://login?token={base64.urlsafe_b64encode(token).decode('ascii')}"
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4
            )
            qr.add_data(qr_url)
            qr.make(fit=True)
            
            # Create QR code image
            img = qr.make_image(fill_color="black", back_color="white")
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            qr_code = base64.b64encode(buffered.getvalue()).decode()
            
            return {
                "status": "success",
                "qr_code": qr_code,
                "token": base64.b64encode(token).decode('ascii'),
                "expires_in": 300  # 5 minutes in seconds
            }
        except Exception as e:
            print(f"Error generating QR code: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def verify_qr_code(self, token: str) -> Dict[str, Any]:
        """Verify QR code login"""
        try:
            await self.connect()
            
            # Check if token is expired
            if self._is_token_expired():
                return {
                    "status": "error",
                    "message": "QR код истек. Пожалуйста, получите новый QR код."
                }
            
            # Verify the token matches
            if base64.b64encode(self._auth_state.get('token', b'')).decode('ascii') != token:
                return {
                    "status": "error",
                    "message": "Неверный токен QR кода"
                }
            
            try:
                result = await self.client(ImportLoginTokenRequest(token=self._auth_state['token']))
                if result.user:
                    try:
                        # Try to sign in with the user from QR code
                        await self.client.sign_in(user=result.user)
                    except SessionPasswordNeededError:
                        # Clear token after successful QR scan
                        self._auth_state.pop('token', None)
                        self._token_expiry = None
                        return {
                            "status": "password_required",
                            "message": "Требуется пароль двухфакторной аутентификации"
                        }
                    except Exception as e:
                        print(f"Error signing in after QR scan: {str(e)}")
                        return {
                            "status": "error",
                            "message": f"Ошибка при завершении авторизации: {str(e)}"
                        }
                    
                    # Clear token after successful login
                    self._auth_state.pop('token', None)
                    self._token_expiry = None
                    return {
                        "status": "success",
                        "message": "Авторизация успешна",
                        "user": result.user
                    }
                return {"status": "pending", "message": "Ожидание сканирования QR-кода"}
            except AuthTokenExpiredError:
                return {
                    "status": "error",
                    "message": "QR код истек. Пожалуйста, получите новый QR код."
                }
        except Exception as e:
            print(f"Error verifying QR code: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def phone_auth(self, phone_number: str, code: Optional[str] = None, password: Optional[str] = None) -> Dict[str, Any]:
        """Phone number authentication"""
        try:
            await self.connect()
            
            if not await self.client.is_user_authorized():
                if not code:
                    try:
                        await self.client.send_code_request(phone_number)
                        return {
                            "status": "code_required",
                            "message": "Код подтверждения отправлен"
                        }
                    except Exception as e:
                        return {"status": "error", "message": f"Ошибка при отправке кода: {str(e)}"}
                
                try:
                    await self.client.sign_in(phone_number, code)
                except SessionPasswordNeededError:
                    if not password:
                        return {
                            "status": "password_required",
                            "message": "Требуется пароль двухфакторной аутентификации"
                        }
                    await self.client.sign_in(password=password)
                except PhoneCodeInvalidError:
                    return {"status": "error", "message": "Неверный код подтверждения"}
            
            return {"status": "success", "message": "Авторизация успешна"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def check_auth(self) -> bool:
        """Check if user is authorized"""
        try:
            await self.connect()
            return await self.client.is_user_authorized()
        except Exception:
            return False

    async def complete_qr_auth(self, password: str) -> Dict[str, Any]:
        """Complete QR code authentication with password"""
        try:
            await self.connect()
            
            if not await self.client.is_user_authorized():
                try:
                    await self.client.sign_in(password=password)
                    return {
                        "status": "success",
                        "message": "Авторизация успешна"
                    }
                except Exception as e:
                    print(f"Error completing QR auth with password: {str(e)}")
                    return {
                        "status": "error",
                        "message": f"Ошибка при вводе пароля: {str(e)}"
                    }
            else:
                return {
                    "status": "success",
                    "message": "Уже авторизован"
                }
        except Exception as e:
            print(f"Error in complete_qr_auth: {str(e)}")
            return {"status": "error", "message": str(e)} 