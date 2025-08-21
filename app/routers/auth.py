# app/routers/base.py
from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import APIRouter, Request, Depends, HTTPException, status

# Seguridad
import jwt
from jwt.exceptions import InvalidTokenError
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError
from pydantic import BaseModel
from app.config import config
import hmac
import hashlib
import base64

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


class AuthException:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Invalid credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    unauthorized_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Unauthorized',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    hmac_validation_failed = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Invalid HMAC',
        headers={'WWW-Authenticate': 'Bearer'},
    )


def verificar_password(plain_password, hashed_password):
    return password_hasher.verify(hashed_password, plain_password)


async def autenticar_usuario(username: str, password: str, session: AsyncSessionDep) -> UsuarioDB | None:
    try:
        usuario = await usuario_query.get_by_username(session, username)
    except InvalidHashError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
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

    try:
        payload = jwt.decode(token, config.secret_key, [config.algorithm])
        user_id = payload.get('sub')
        if user_id is None:
            raise AuthException.unauthorized_exception
    except InvalidTokenError:
        raise AuthException.unauthorized_exception
    user = await usuario_query.get(session, user_id)
    if user is None:
        raise AuthException.unauthorized_exception
    return user


# Webhooks Shopify
async def hmac_validation_shopify(request: Request) -> bool:
    """
    Valida una firma de webhook de Shopify transcribiendo la lógica
    oficial de la documentación de Shopify (Node.js) a Python.
    https://shopify.dev/docs/apps/build/webhooks/subscribe/https#step-2-validate-the-origin-of-your-webhook-to-ensure-its-coming-from-shopify
    """
    # 1. Calcular el digest HMAC-SHA256.
    # Se utiliza el secreto (codificado a bytes) como clave y el cuerpo crudo de la
    # solicitud como mensaje.
    body = await request.body()
    received_hmac = request.headers.get('x-shopify-hmac-sha256', '')
    calculated_hmac_digest = hmac.new(
        config.webhook_secret_shopify.encode('utf-8'), msg=body, digestmod=hashlib.sha256
    ).digest()

    # 2. Codificar el digest en Base64.
    # El resultado del digest se codifica en Base64 para que coincida con el formato
    # del encabezado que envía Shopify.
    calculated_hmac_base64 = base64.b64encode(calculated_hmac_digest).decode('utf-8')

    # 3. Comparar de forma segura (timing-safe) el HMAC calculado con el recibido.
    # hmac.compare_digest previene ataques de temporización.
    verify =  hmac.compare_digest(calculated_hmac_base64, received_hmac)
    if not verify:
        raise AuthException.hmac_validation_failed
    return True


@router.post('/login')
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: AsyncSessionDep) -> Token:
    usuario = await autenticar_usuario(form_data.username, form_data.password, session)
    if not usuario:
        raise AuthException.credentials_exception
    data = {'sub': str(usuario.id), 'name': usuario.username}
    token = crear_access_token(data)
    return Token(access_token=token, token_type='bearer')
