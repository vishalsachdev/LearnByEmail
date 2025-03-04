from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str
    confirm_password: str


class UserLogin(UserBase):
    password: str


class UserPasswordReset(BaseModel):
    email: EmailStr


class UserResetToken(BaseModel):
    token: str
    status: str = "success"
    message: str = "Password reset email sent"


class UserResetPassword(BaseModel):
    token: str
    password: str
    confirm_password: str


class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: int