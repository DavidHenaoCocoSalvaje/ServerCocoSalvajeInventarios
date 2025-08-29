# app/internal/query/usuario.py
from getpass import getpass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from argon2 import PasswordHasher

from app.models.db.usuario import UsuarioCreate, UsuarioDB
from app.models.db.session import get_async_session

from app.internal.query.base import BaseQuery
from app.internal.log import factory_logger
from app.config import config


class UsuarioQuery(BaseQuery[UsuarioDB, UsuarioCreate]):
    """Repositorio para la entidad Usuario"""

    def __init__(self):
        super().__init__(UsuarioDB, UsuarioCreate)

    async def get_by_username(self, session: AsyncSession, username: str):
        """Obtiene un usuario por su documento de identidad"""
        statement = select(self.model_db).where(self.model_db.username == username)
        results = await session.execute(statement)
        scalar_results = results.scalars()
        return scalar_results.one_or_none()


usuario_query = UsuarioQuery()
password_hasher = PasswordHasher()


usuario_logger = factory_logger('usuario', file=True)


async def set_admin_user(reset_password: bool = False):
    logger = factory_logger('main', file=False)
    session_gen = get_async_session()
    session: AsyncSession = await anext(session_gen)

    try:
        usuario = await usuario_query.get_by_username(session, 'admin')
        if usuario is None:
            password = password_hasher.hash(config.admin_password)
            usuario = UsuarioDB(username='admin', password=password)
            usuario = await usuario_query.create(session, usuario)
            logger.info('✅ Usuario creado')
        if reset_password:
            password = getpass('Ingrese una contraseña para el usuario admin:\n')
            retype_password = getpass('Confirme la contraseña:\n')
            if password != retype_password:
                logger.error('❌ Las contraseñas no coinciden. Por favor, vuelva a intentarlo.')
                return await set_admin_user(reset_password=reset_password)
            usuario.password = password_hasher.hash(password)
            usuario_db = await usuario_query.get_by_username(session, 'admin')
            if usuario_db is None:
                usuario_db = await usuario_query.create(session, usuario)

            if usuario_db.id is None:
                exception = ValueError('No se pudo obtener el ID del usuario')
                usuario_logger.error(f'{exception}')
                raise exception

            await usuario_query.update(session, usuario_db, usuario, usuario_db.id)
    finally:
        # Cerrar el generador para limpiar la sesión
        await session_gen.aclose()
