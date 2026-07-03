import os
import jwt
from fastapi import APIRouter, Depends, HTTPException
from datetime import timedelta, datetime, timezone
from app.services.auth import login_user, register_user
from pydantic import BaseModel
from starlette import status
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm
from app.dependencies import get_current_user

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


class RegisterUserRequest(BaseModel):
    email: str
    password: str
    name: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def create_user(request: RegisterUserRequest):
    result = register_user(email=request.email, password=request.password, name=request.name)
    if not result:
        raise HTTPException(status_code=400, detail="Requirements Not Met!")
    return {'message': "user registration successful"}


@router.post("/login", response_model=LoginResponse)
async def user_login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> LoginResponse:
    result = login_user(form_data.username, form_data.password)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid Credentials")
    token = create_user_access_token(result.user_id, result.email, timedelta(days=15))
    return LoginResponse(
        access_token=token,
        token_type='bearer'
    )


def create_user_access_token(user_id, email, time):
    time = datetime.now(timezone.utc) + time
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": time
    }
    return jwt.encode(payload, os.getenv('JWT_KEY'), os.getenv('JWT_ALG'))


@router.get("/me")
async def get_me(user_id: Annotated[int, Depends(get_current_user)]):
    return user_id
