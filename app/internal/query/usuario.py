# app/internal/query/usuario.py
from sqlalchemy.ext.asyncio import AsyncSession

from sqlmodel import select

from app.models.db.usuario import UsuarioDB
from app.internal.query.base import BaseQuery


class UsuarioQuery(BaseQuery[UsuarioDB]):
    """Repositorio para la entidad Usuario"""

    def __init__(self):
        super().__init__(UsuarioDB)

    async def get_by_username(self, session: AsyncSession, username: str):
        """Obtiene un usuario por su documento de identidad"""
        statement = select(self.model).where(self.model.username == username)
        results = await session.execute(statement)
        scalar_results = results.scalars()
        return scalar_results.one_or_none()


usuario_query = UsuarioQuery()
