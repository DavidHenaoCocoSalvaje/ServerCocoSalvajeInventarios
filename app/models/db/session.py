# app/models/base.py

# Inyeccion de dependencias
from fastapi import Depends
from typing import Annotated

from typing import AsyncGenerator

from sqlalchemy import URL, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlmodel import SQLModel


from app.config import config

# SQLModel.metadata.schema = 'public'  # Asegúrate de que todas las tablas se creen en el esquema correcto
url = URL.create(
    'postgresql+psycopg',
    username=config.db_user,
    password=config.db_password,
    host=config.db_host,
    port=config.db_port,
    database=config.db_name,
)

async_engine = create_async_engine(url)


AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Necesario para FastAPI para acceder a objetos después del commit
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]


async def create_db_and_tables():
    """Crea los esquemas y las tablas de la base de datos si no existen."""
    async with async_engine.begin() as conn:
        # Crear schema si no existe
        await conn.execute(text('CREATE SCHEMA IF NOT EXISTS transaccion'))
        await conn.execute(text('CREATE SCHEMA IF NOT EXISTS public'))
        await conn.execute(text('CREATE SCHEMA IF NOT EXISTS inventario'))

        # Crear todas las tablas
        await conn.run_sync(SQLModel.metadata.create_all)
