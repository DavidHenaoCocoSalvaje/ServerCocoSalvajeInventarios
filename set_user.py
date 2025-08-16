import asyncio

from app.internal.query.usuario import usuario_query
from app.models.db.usuario import UsuarioCreate
from app.models.db.session import get_async_session
from app.internal.log import factory_logger


logger = factory_logger('set_user', file=False)


async def set_user():
    password = input('Contraseña:')

    usuario = UsuarioCreate(username='admin', password=password)

    session_gen = get_async_session()
    session = await anext(session_gen)

    try:
        user = await usuario_query.create(session, usuario)
        await session.commit()  # Importante: hacer commit para persistir los cambios
        logger.info(f'✅ Usuario creado con ID {user.id}')
    finally:
        # Cerrar el generador para limpiar la sesión
        await session_gen.aclose()


if __name__ == '__main__':
    asyncio.run(set_user())
