# backend/app/schemas/user_schema.py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(min_length=4, max_length=50)
    nickname: str = Field(min_length=1, max_length=50)
    profile_image: Optional[str] = None


class UserLogin(UserBase):
    email:str
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    nickname: str
    profile_image: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True  # Pydantic v1: orm_mode = True
        orm_mode = True



class UserUpdate(BaseModel):
    nickname: str = Field(min_length=1, max_length=50)
    profile_image: Optional[str] = None

class UserPasswordUpdate(BaseModel):
    new_password: str