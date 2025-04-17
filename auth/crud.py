from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from . import models, schemas
from .utils import get_password_hash, verify_password

def get_user(db: Session, username: str) -> Optional[models.User]:
    """Получить пользователя по имени пользователя"""
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """Получить пользователя по email"""
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
    """Получить пользователя по ID"""
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    """Получить список пользователей с пагинацией"""
    return db.query(models.User).offset(skip).limit(limit).all()

def search_users(db: Session, query: str) -> List[models.User]:
    """Поиск пользователей по имени или email"""
    return db.query(models.User).filter(
        or_(
            models.User.username.ilike(f"%{query}%"),
            models.User.email.ilike(f"%{query}%")
        )
    ).all()

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    """Создать нового пользователя"""
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        disabled=False
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate) -> Optional[models.User]:
    """Обновить информацию о пользователе"""
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None
    
    update_data = user_update.dict(exclude_unset=True)
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int) -> bool:
    """Удалить пользователя"""
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return False
    
    db.delete(db_user)
    db.commit()
    return True

def authenticate_user(db: Session, username: str, password: str) -> Optional[models.User]:
    """Аутентификация пользователя"""
    user = get_user(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def change_password(db: Session, user_id: int, old_password: str, new_password: str) -> bool:
    """Сменить пароль пользователя"""
    user = get_user_by_id(db, user_id)
    if not user:
        return False
    
    if not verify_password(old_password, user.hashed_password):
        return False
    
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    return True

def toggle_user_status(db: Session, user_id: int) -> Optional[models.User]:
    """Включить/выключить пользователя"""
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    
    user.disabled = not user.disabled
    db.commit()
    db.refresh(user)
    return user