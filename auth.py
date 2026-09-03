import os
import hashlib
import secrets
import datetime
import jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
import models

SECRET_KEY = 'juice-shop-super-secret-key-2026-safe-and-fresh'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_DAYS = 7

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/auth/login', auto_error=False)

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return f'{salt}:{key.hex()}'

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        salt, key_hex = hashed_password.split(':')
        key = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return secrets.compare_digest(key.hex(), key_hex)
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: datetime.timedelta = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_token_from_request(request: Request, token: str = Depends(oauth2_scheme)) -> str:
    if token:
        return token
    # Check authorization header
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header.split(' ')[1]
    # Check cookie
    cookie_token = request.cookies.get('access_token')
    if cookie_token:
        return cookie_token
    return None

def get_current_user_optional(request: Request, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    resolved_token = get_token_from_request(request, token)
    if not resolved_token:
        return None
    try:
        payload = jwt.decode(resolved_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get('sub')
        if email is None:
            return None
    except Exception:
        return None

    user = db.query(models.User).filter(models.User.email == email).first()
    return user

def get_current_user(request: Request, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = get_current_user_optional(request, token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Not authenticated. Please log in.',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    return user

def get_session_id(request: Request) -> str:
    session_id = request.cookies.get('juice_session_id')
    if not session_id:
        session_id = request.headers.get('X-Session-ID')
    return session_id or ''
