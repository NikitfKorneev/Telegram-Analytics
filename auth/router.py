# router.py
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Response
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from . import schemas, crud, models, utils
from .database import get_db
from .dependencies import get_current_active_user
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
async def read_users_me(current_user: models.User = Depends(utils.get_current_user)):
    try:
        return current_user
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )

@router.post("/files/")
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
async def read_file(
    file_id: int,
    current_user: models.User = Depends(utils.get_current_user),
    db: Session = Depends(get_db)
):
    try:
        file = crud.get_file(db, file_id=file_id)
        if file is None:
            raise HTTPException(status_code=404, detail="File not found")
        if file.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        return file
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )

@router.delete("/files/{file_id}")
async def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    try:
        file = crud.get_file(db, file_id)
        if not file or file.owner_id != current_user.id:
            raise HTTPException(status_code=404, detail="File not found")
        
        if crud.delete_file(db, file_id):
            return {"message": "File deleted successfully"}
        raise HTTPException(status_code=500, detail="Error deleting file")
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )