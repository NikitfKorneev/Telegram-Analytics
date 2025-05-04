from functools import wraps
from fastapi import HTTPException, status
from .models import User

def require_permission(permission_name: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: User = None, **kwargs):
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Проверяем, есть ли у пользователя нужное разрешение
            user_permissions = [p.name for p in current_user.role.permissions]
            if permission_name not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission_name}' required"
                )
            
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator 