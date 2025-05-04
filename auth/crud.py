from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import List, Optional
from . import models, schemas
from .utils import get_password_hash, verify_password
from fastapi import HTTPException
from datetime import datetime

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).options(
        joinedload(models.User.role).joinedload(models.Role.permissions)
    ).offset(skip).limit(limit).all()

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def search_users(db: Session, query: str) -> List[models.User]:
    """Поиск пользователей по имени или email"""
    return db.query(models.User).filter(
        or_(
            models.User.username.ilike(f"%{query}%"),
            models.User.email.ilike(f"%{query}%")
        )
    ).all()

def create_user(db: Session, user: schemas.UserCreate):
    try:
        hashed_password = get_password_hash(user.password)
        db_user = models.User(
            username=user.username,
            email=user.email,
            hashed_password=hashed_password,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creating user: {str(e)}"
        )

def update_user(db: Session, user_id: int, user: schemas.UserUpdate):
    db_user = get_user(db, user_id)
    if db_user:
        for key, value in user.dict(exclude_unset=True).items():
            setattr(db_user, key, value)
        db_user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    db_user = get_user(db, user_id)
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user

def authenticate_user(db: Session, username: str, password: str) -> Optional[models.User]:
    """Аутентификация пользователя"""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def change_password(db: Session, user_id: int, old_password: str, new_password: str) -> bool:
    """Сменить пароль пользователя"""
    user = get_user(db, user_id)
    if not user:
        return False
    
    if not verify_password(old_password, user.hashed_password):
        return False
    
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    return True

def toggle_user_status(db: Session, user_id: int) -> Optional[models.User]:
    """Включить/выключить пользователя"""
    user = get_user(db, user_id)
    if not user:
        return None
    
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    return user

def get_user_files(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.File).filter(models.File.owner_id == user_id).offset(skip).limit(limit).all()

def get_file(db: Session, file_id: int):
    return db.query(models.File).filter(models.File.id == file_id).first()

def get_files_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.File).filter(models.File.owner_id == user_id).offset(skip).limit(limit).all()

def create_file(db: Session, file: schemas.FileCreate, user_id: int):
    db_file = models.File(
        filename=file.filename,
        content=file.content,
        is_public=file.is_public,
        owner_id=user_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

def update_file(db: Session, file_id: int, file: schemas.FileUpdate):
    db_file = get_file(db, file_id)
    if db_file:
        for key, value in file.dict(exclude_unset=True).items():
            setattr(db_file, key, value)
        db_file.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_file)
    return db_file

def delete_file(db: Session, file_id: int):
    file = get_file(db, file_id)
    if file:
        db.delete(file)
        db.commit()
        return True
    return False