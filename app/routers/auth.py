# app/routers/base.py
from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status

# Seguridad
import jwt
from jwt.exceptions import InvalidTokenError
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from argon2 import PasswordHasher
from pydantic import BaseModel
from app.config import config

# Models
from app.models.db.usuario import UsuarioDB

# Repository
from app.internal.query.usuario import usuario_query

# Session
from app.models.db.session import AsyncSessionDep

router = APIRouter(
    prefix='/auth',
    tags=['Auth'],
    responses={404: {'description': 'No encontrado'}},
)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None
    scopes: list[str] = []


password_hasher = PasswordHasher()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/login')


def verificar_password(plain_password, hashed_password):
    return password_hasher.verify(hashed_password, plain_password)


async def autenticar_usuario(username: str, password: str, session: AsyncSessionDep) -> UsuarioDB | None:
    usuario = await usuario_query.get_by_username(session, username)
    if usuario and verificar_password(password, usuario.password):
        return usuario
    return None


def crear_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=3)
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, config.secret_key, algorithm=config.algorithm)
    return encoded_jwt


async def validar_access_token(token: Annotated[str, Depends(oauth2_scheme)], session: AsyncSessionDep):
    """Se obtiene el usuario actual a partir del token JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Invalid credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    try:
        payload = jwt.decode(token, config.secret_key, [config.algorithm])
        user_id = payload.get('sub')
        if user_id is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    user = await usuario_query.get(session, user_id)
    if user is None:
        raise credentials_exception
    return user


@router.post('/login')
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: AsyncSessionDep) -> Token:
    usuario = await autenticar_usuario(form_data.username, form_data.password, session)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Usuario o contraseña incorrectos',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    data = {'sub': str(usuario.id), 'name': usuario.username}
    token = crear_access_token(data)
    return Token(access_token=token, token_type='bearer')
