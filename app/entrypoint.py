# app/entrypoint.py
if __name__ == "__main__":
    from os.path import abspath
    from sys import path as sys_path
    sys_path.append(abspath('.'))

from app.models.db.session import create_db_and_tables
from app.internal.query.inventario import seed_data_inventario
from app.internal.query.usuario import set_admin_user

async def init_db():
    print("⏳ Inicializando base de datos...")
    await create_db_and_tables()
    await set_admin_user()
    await seed_data_inventario()
    print("✅ Base de datos lista.")

if __name__ == "__main__":
    from asyncio import run
    run(init_db())