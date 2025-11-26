# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import inventario, transacciones, usuario, auth, search, facturacion
from app.internal.log import factory_logger

logger = factory_logger('main', file=False)

# Crea la instancia de la aplicación FastAPI
app = FastAPI(
    title='API de Inventarios Coco Salvaje',
    description='API para gestionar el inventario de Coco Salvaje.',
    version='1.0.0',
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
app.include_router(inventario.shopify_inventario_router)
app.include_router(transacciones.router)
# Busqueda en internet
app.include_router(search.router)
# Facturación
app.include_router(facturacion.router)


# Ruta raíz simple para verificar que la API está funcionando
@app.get('/', tags=['Root'])
async def read_root():
    """Ruta raíz de la API."""
    return {'message': 'API Coco Salvaje'}
