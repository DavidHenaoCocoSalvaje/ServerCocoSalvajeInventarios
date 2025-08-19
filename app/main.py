# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager


from app.routers import usuario
from app.routers import auth
from app.routers import inventario
from app.models.db.session import create_db_and_tables
from app.internal.log import factory_logger
from app.internal.query.inventario import seed_data_inventario
from app.internal.query.usuario import set_admin_user

logger = factory_logger('main', file=False)


# --- Ciclo de vida de la aplicación (Opcional) ---
# Puedes usar lifespan para tareas de inicio/apagado, como crear tablas
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('Iniciando aplicación y base de datos...')
    await create_db_and_tables()
    await set_admin_user()
    await seed_data_inventario()
    logger.info('Base de datos lista.')
    yield  # La aplicación se ejecuta aquí
    logger.info('Cerrando aplicación...')


# Crea la instancia de la aplicación FastAPI
app = FastAPI(
    title='API de Inventarios Coco Salvaje',
    description='API para gestionar el inventario de Coco Salvaje.',
    version='1.0.0',
    lifespan=lifespan,  # Usa el contexto de vida para crear tablas
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Incluye el router de usuarios en la aplicación principal
app.include_router(usuario.router)
# Incluye el router de autenticación en la aplicación principal
app.include_router(auth.router)
# Incluye el router de elementos de inventario y shopify
app.include_router(inventario.router)
app.include_router(inventario.shopify_router)


# Ruta raíz simple para verificar que la API está funcionando
@app.get('/', tags=['Root'])
async def read_root():
    """Ruta raíz de la API."""
    return {'message': 'API Coco Salvaje'}


# --- Instrucciones para Ejecutar (en comentario) ---
# 1. Asegúrate de tener PostgreSQL corriendo y la base de datos creada.
# 2. Configura la variable de entorno DATABASE_URL (en .env o directamente).
#    Ejemplo: export DATABASE_URL="postgresql+psycopg://user:password@host:port/db"
# 3. Ejecuta el servidor con Uvicorn:
#    uvicorn main:app --reload --host 0.0.0.0 --port 8000
#    --reload: Recarga automáticamente al detectar cambios en el código.
#    --host 0.0.0.0: Hace accesible la API desde otras máquinas en la red.
#    --port 8000: Puerto en el que correrá la API.
# 4. Accede a la documentación interactiva en: http://localhost:8000/docs
