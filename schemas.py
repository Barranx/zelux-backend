from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr


# ------- USER --------
class UserBase(BaseModel):
    email: EmailStr
    full_name: str


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(UserBase):
    id: int
    is_admin: bool
    created_at: datetime

    class Config:
        orm_mode = True


# ------- CONTACT / MESSAGE --------
class ContactIn(BaseModel):
    nome: str
    email: EmailStr
    messaggio: str


class MessageOut(BaseModel):
    id: int
    nome: str
    email: EmailStr
    contenuto: str
    created_at: datetime
    user_id: Optional[int] = None

    class Config:
        orm_mode = True


# ------- AUTH TOKEN -------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
