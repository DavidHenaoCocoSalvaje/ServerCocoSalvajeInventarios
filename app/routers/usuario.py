# app/routers/usuario.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from string import punctuation

# Modelos
from app.models.db.session import AsyncSessionDep
from app.models.db.usuario import UsuarioBase, UsuarioCreate, UsuarioDB

# Base de datos (Repositorio)
from app.internal.query.usuario import usuario_query

# Seguridad
from app.routers.auth import password_hasher, validar_access_token

router = APIRouter(
    prefix='/usuarios',
    tags=['Usuarios'],
    responses={404: {'description': 'No encontrado'}},
    dependencies=[Depends(validar_access_token)],
)


def verificar_complejidad_password(usuario: UsuarioCreate):
    # - mínimo 8 caracteres
    # - mínimo 1 número
    # - mínimo 1 letra mayúscula
    # - mínimo 1 letra minúscula
    # - mínimo 1 caracter especial
    if len(usuario.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='La contraseña debe tener al menos 8 caracteres.',
        )
    if not any(char.isdigit() for char in usuario.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='La contraseña debe contener al menos un número.',
        )
    if not any(char.isupper() for char in usuario.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='La contraseña debe contener al menos una letra mayúscula.',
        )
    if not any(char.islower() for char in usuario.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='La contraseña debe contener al menos una letra minúscula.',
        )
    if not any(char in punctuation for char in usuario.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='La contraseña debe contener al menos un caracter especial.',
        )
    return usuario


@router.post(
    '/',
    response_model=UsuarioBase,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    status_code=status.HTTP_201_CREATED,
    summary='Crear un nuevo usuario',
    description='Crea un nuevo usuario en la base de datos.',
)
async def crear_usuario(
    usuario: UsuarioCreate,
    session: AsyncSessionDep,
):
    # hash password
    usuario.password = password_hasher.hash(usuario.password)
    usuario_db = UsuarioDB(**usuario.model_dump())

    usuario_creado = await usuario_query.create(session, usuario_db)
    return usuario_creado


@router.get(
    '/',
    response_model=UsuarioBase,
    response_model_exclude_none=True,
    summary='Obtener lista de usuarios',
    description='Obtiene una lista paginada de usuarios registrados.',
)
async def get_usuarios(
    session: AsyncSessionDep,
    skip: int = 0,
    limit: int = 100,
):
    usuarios = await usuario_query.get_list(session=session, skip=skip, limit=limit)
    return usuarios


@router.get(
    '/{usuario_id}',
    response_model=UsuarioBase,
    summary='Obtener un usuario por ID',
    description='Obtiene los detalles de un usuario específico mediante su ID.',
)
async def get(session: AsyncSessionDep, usuario_id: int):
    db_usuario = await usuario_query.get(session, usuario_id)
    if db_usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'UsuarioBase con ID {usuario_id} no encontrado',
        )
    return db_usuario


@router.put(
    '/{usuario_id}',
    response_model=UsuarioBase,
    summary='Actualizar un usuario',
)
async def actualizar(
    session: AsyncSessionDep,
    usuario_id: int,
    usuario: UsuarioBase,
):
    db_user = await usuario_query.get(session, usuario_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Usuario no encontrado',
        )
    usuario_actualizado = await usuario_query.update(session, db_user, usuario)
    return usuario_actualizado


@router.delete(
    '/{usuario_id}',
    response_model=UsuarioBase,
    summary='Eliminar un usuario',
)
async def eliminar(
    session: AsyncSessionDep,
    usuario_id: int,
):
    usuario_eliminado = await usuario_query.delete(session, usuario_id)
    if usuario_eliminado is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Usuario no encontrado',
        )
    return usuario_eliminado
