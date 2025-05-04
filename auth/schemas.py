from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class TokenData(BaseModel):
    email: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class Role(RoleBase):
    id: int
    permissions: List["Permission"] = []

    class Config:
        from_attributes = True

class PermissionBase(BaseModel):
    name: str
    description: Optional[str] = None

class Permission(PermissionBase):
    id: int

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    username: str
    email: EmailStr
    is_active: bool = True

class UserCreate(UserBase):
    password: str
    confirm_password: str

class UserUpdate(UserBase):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class User(UserBase):
    id: int
    role_id: Optional[int] = None
    role: Optional[Role] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class FileBase(BaseModel):
    filename: str
    content: str
    is_public: bool = False

class FileCreate(FileBase):
    pass

class FileUpdate(FileBase):
    filename: Optional[str] = None
    content: Optional[str] = None
    is_public: Optional[bool] = None

class File(FileBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ChatFileBase(BaseModel):
    filename: str

class ChatFileCreate(ChatFileBase):
    content: str

class ChatFile(ChatFileBase):
    id: int
    file_path: str
    created_at: datetime
    user_id: int

    class Config:
        from_attributes = True