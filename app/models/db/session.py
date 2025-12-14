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


from app.config import Config

# SQLModel.metadata.schema = 'public'  # Asegúrate de que todas las tablas se creen en el esquema correcto
url = URL.create(
    'postgresql+psycopg',
    username=Config.db_user,
    password=Config.db_password,
    host=Config.db_host,
    port=Config.db_port,
    database=Config.db_name,
)

async_engine = create_async_engine(url, pool_size=50)

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
        await conn.execute(text("SET timezone = 'America/Bogota'"))
        await conn.execute(text('CREATE SCHEMA IF NOT EXISTS public'))
        await conn.execute(text('CREATE SCHEMA IF NOT EXISTS inventario'))
        await conn.execute(text('CREATE SCHEMA IF NOT EXISTS transaccion'))

        # Crear todas las tablas
        await conn.run_sync(SQLModel.metadata.create_all)
