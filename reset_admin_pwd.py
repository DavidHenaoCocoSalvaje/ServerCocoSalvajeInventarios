import asyncio
from app.internal.log import factory_logger
from app.internal.query.usuario import set_admin_user


logger = factory_logger('set_user', file=False)


async def reset_admin_pwd():
    await set_admin_user(reset_password=True)
    logger.info('✅ Contraseña del usuario admin restablecida.')


if __name__ == '__main__':
    asyncio.run(set_admin_user(reset_password=True))
