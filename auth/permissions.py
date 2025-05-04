from functools import wraps
from fastapi import HTTPException, status
from auth.dependencies import get_current_active_user
from auth.models import User

def require_permission(permission_name: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: User = None, **kwargs):
            if not current_user:
                current_user = await get_current_active_user()
            
            # Check if user has the required permission
            user_permissions = [p.name for p in current_user.role.permissions]
            if permission_name not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission_name}' required"
                )
            
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator 