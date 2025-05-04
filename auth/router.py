# router.py
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Response
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session, joinedload
from . import schemas, crud, models, utils
from .database import get_db
from .dependencies import get_current_active_user
from .decorators import require_permission
import os

router = APIRouter(tags=["auth"])

@router.post("/register", response_model=schemas.User)
async def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        # Проверяем пароли
        if user.password != user.confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match")
            
        # Проверяем существующего пользователя по email
        db_user = crud.get_user_by_email(db, email=user.email)
        if db_user:
            raise HTTPException(status_code=400, detail="Email already registered")
            
        # Проверяем существующего пользователя по username
        db_user = crud.get_user_by_username(db, username=user.username)
        if db_user:
            raise HTTPException(status_code=400, detail="Username already registered")
        
        # Создаем пользователя
        return crud.create_user(db=db, user=user)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    try:
        user = crud.authenticate_user(db, form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token = utils.create_access_token(data={"sub": user.email})
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )

@router.get("/users/me")
@require_permission("view_profile")
async def read_users_me(current_user: models.User = Depends(utils.get_current_user)):
    try:
        return current_user
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )

@router.post("/files/")
@require_permission("create_file")
async def create_file(
    file: schemas.FileCreate,
    current_user: models.User = Depends(utils.get_current_user),
    db: Session = Depends(get_db)
):
    try:
        return crud.create_file(db=db, file=file, user_id=current_user.id)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )

@router.get("/files/{file_id}")
@require_permission("view_file")
async def read_file(
    file_id: int,
    current_user: models.User = Depends(utils.get_current_user),
    db: Session = Depends(get_db)
):
    try:
        file = crud.get_file(db, file_id=file_id)
        if file is None:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Проверяем права доступа к файлу
        if file.owner_id != current_user.id:
            # Проверяем, есть ли у пользователя право просматривать все файлы
            if "view_all_files" not in [p.name for p in current_user.role.permissions]:
                raise HTTPException(status_code=403, detail="Not enough permissions")
        
        return file
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )

@router.delete("/files/{file_id}")
@require_permission("delete_file")
async def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    try:
        file = crud.get_file(db, file_id)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Проверяем права доступа к файлу
        if file.owner_id != current_user.id:
            # Проверяем, есть ли у пользователя право управлять всеми файлами
            if "manage_system" not in [p.name for p in current_user.role.permissions]:
                raise HTTPException(status_code=403, detail="Not enough permissions")
        
        if crud.delete_file(db, file_id):
            return {"message": "File deleted successfully"}
        raise HTTPException(status_code=500, detail="Error deleting file")
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )

# Добавляем новые эндпоинты для управления пользователями (только для админов)
@router.get("/users/")
@require_permission("manage_users")
async def get_users(
    current_user: models.User = Depends(utils.get_current_user),
    db: Session = Depends(get_db)
):
    users = db.query(models.User).options(
        joinedload(models.User.role).joinedload(models.Role.permissions)
    ).all()
    return users

@router.get("/users/{user_id}")
@require_permission("manage_users")
async def get_user(
    user_id: int,
    current_user: models.User = Depends(utils.get_current_user),
    db: Session = Depends(get_db)
):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/users/{user_id}")
@require_permission("manage_users")
async def update_user_role(
    user_id: int,
    role_id: int,
    current_user: models.User = Depends(utils.get_current_user),
    db: Session = Depends(get_db)
):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    user.role_id = role_id
    db.commit()
    db.refresh(user)
    return user

@router.post("/users/{user_id}/reset-password")
@require_permission("manage_users")
async def reset_user_password(
    user_id: int,
    password_data: dict,
    current_user: models.User = Depends(utils.get_current_user),
    db: Session = Depends(get_db)
):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    hashed_password = utils.get_password_hash(password_data["new_password"])
    user.hashed_password = hashed_password
    db.commit()
    return {"message": "Password updated successfully"}

@router.delete("/users/{user_id}")
@require_permission("manage_users")
async def delete_user(
    user_id: int,
    current_user: models.User = Depends(utils.get_current_user),
    db: Session = Depends(get_db)
):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}