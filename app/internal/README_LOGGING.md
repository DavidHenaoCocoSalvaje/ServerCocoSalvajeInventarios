# Sistema de Logging - CocoSalvaje Inventarios

Este documento explica cómo usar el sistema de logging implementado en la aplicación, que se configura automáticamente según el ambiente de ejecución usando la configuración centralizada de `config.py`.

## Configuración por Ambiente

### 🚀 Producción (Azure Container Apps)
- **Configuración**: `ENVIRONMENT=production` o `ENVIRONMENT=prod`
- **Logs**: Solo **consola** con nivel **INFO**
- **Propósito**: Los logs van directamente a los logs del contenedor Docker en Azure
- **Variables Azure automáticas** (proporcionadas por Azure Container Apps):
  - `CONTAINER_APP_NAME`: Nombre del container app
  - `CONTAINER_APP_REVISION`: Nombre de la revisión
  - `CONTAINER_APP_HOSTNAME`: Hostname específico de la revisión
  - `CONTAINER_APP_ENV_DNS_SUFFIX`: Sufijo DNS del ambiente
  - `CONTAINER_APP_REPLICA_NAME`: Nombre de la réplica del container
  - `CONTAINER_APP_JOB_NAME`: Nombre del job (si aplica)
  - `CONTAINER_APP_JOB_EXECUTION_NAME`: Nombre de la ejecución del job (si aplica)

### 🛠️ Desarrollo (Local)
- **Configuración**: `ENVIRONMENT=development` o `ENVIRONMENT=dev` (por defecto)
- **Logs**: 
  - **Archivo**: `logs/app.log` con nivel **INFO** (rotación 10MB, 5 respaldos)
  - **Consola**: Nivel **DEBUG** para desarrollo detallado

## Variables de Ambiente

Todas las variables se configuran en `config.py` para evitar imports de `os` en otros lugares.

Agrega a tu archivo `.env`:

```bash
# Para desarrollo local (por defecto)
ENVIRONMENT=development

# Para producción en Azure Container Apps
ENVIRONMENT=production

# Las siguientes variables son proporcionadas AUTOMÁTICAMENTE por Azure Container Apps:
# CONTAINER_APP_NAME=mi-container-app
# CONTAINER_APP_REVISION=mi-container-app--20mh1s9
# CONTAINER_APP_HOSTNAME=mi-container-app--20mh1s9.defaultdomain.region.azurecontainerapps.io
# CONTAINER_APP_ENV_DNS_SUFFIX=defaultdomain.region.azurecontainerapps.io
# CONTAINER_APP_REPLICA_NAME=mi-container-app--20mh1s9-86c8c4b497-zx9bq
```

## Características

- **Configuración centralizada** en `config.py`
- **Sin imports de `os`** en módulos de logging
- **Variables automáticas de Azure Container Apps**: Se detectan automáticamente sin configuración
- **Detección robusta** del ambiente usando variables built-in de Azure
- **Optimizado para Azure Container Apps**
- **Configuración diferente** por ambiente
- **Singleton Pattern**: Una sola instancia de logger
- **Rotación de archivos** solo en desarrollo

> **Nota importante**: Las variables de Azure Container Apps (`CONTAINER_APP_*`) son proporcionadas automáticamente por Azure cuando tu aplicación se ejecuta en un Container App. No necesitas configurarlas manualmente.

## Estructura de Archivos

```
logs/
├── app.log          # Archivo principal de logs
├── app.log.1        # Respaldo 1
├── app.log.2        # Respaldo 2
└── ...              # Hasta 5 respaldos
```

### Verificar el Ambiente Actual

```python
from app.internal.log import get_current_environment
from app.config import config

# Verificar qué ambiente está detectando
ambiente = get_current_environment()
print(f"Ambiente actual: {ambiente}")  # 'production' o 'development'

# También puedes usar el config directamente
print(f"Es producción: {config.is_production()}")
print(f"Es Azure Container: {config.is_azure_container()}")

# Ver información detallada de Azure Container Apps
azure_info = config.get_azure_container_info()
print(f"Info Azure Container: {azure_info}")
```

## Uso Básico

### Importar el logger

```python
from app.internal.log import get_logger, Logger
```

### Logger principal

```python
# Logger principal de la aplicación
logger = get_logger()
logger.info("Mensaje informativo")
logger.warning("Mensaje de advertencia")
logger.error("Mensaje de error")
logger.debug("Mensaje de debug")
```

### Loggers específicos por módulo

```python
# Logger específico para un módulo
inventario_logger = get_logger("inventario")
inventario_logger.info("Operación de inventario completada")

# Logger para Shopify
shopify_logger = get_logger("shopify")
shopify_logger.info("Sincronización con Shopify iniciada")

# Logger para base de datos
db_logger = get_logger("database")
db_logger.debug("Query ejecutado correctamente")
```

### Instancias directas de Logger

```python
# Crear instancia directa de Logger
api_logger = Logger("api")
api_logger.logger.info("Endpoint API llamado")

# Acceder al logger usando la propiedad
auth_logger = Logger("auth")
auth_logger.logger.warning("Intento de acceso fallido")
```

## Ejemplos Prácticos

### 1. En un Router de FastAPI

```python
from fastapi import APIRouter, HTTPException
from app.internal.log import get_logger
import time

# Logger específico para el router de inventario
logger = get_logger("inventario")

router = APIRouter()

@router.get("/productos")
async def get_productos():
    start_time = time.time()
    
    try:
        logger.info("Iniciando consulta de productos")
        
        # Lógica del endpoint
        productos = await consultar_productos()
        
        duration = time.time() - start_time
        logger.info(f"Consulta exitosa: {len(productos)} productos en {duration:.3f}s")
        
        return productos
        
    except Exception as e:
        duration = time.time() - start_time
        logger.exception(f"Error al consultar productos (duración: {duration:.3f}s)")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
```

### 2. En Operaciones de Base de Datos

```python
from app.internal.log import get_logger
import time

db_logger = get_logger("database")

async def ejecutar_query(query: str, params: dict):
    start_time = time.time()
    
    try:
        db_logger.debug(f"Ejecutando query: {query}")
        
        # Ejecutar query
        result = await database.execute(query, params)
        
        duration = time.time() - start_time
        db_logger.info(f"Query ejecutado exitosamente - Duración: {duration:.3f}s - Filas afectadas: {result.rowcount}")
        
        return result
        
    except Exception as e:
        duration = time.time() - start_time
        db_logger.error(f"Error en query (duración: {duration:.3f}s): {str(e)}")
        raise
```

### 3. En Sincronización con Shopify

```python
from app.internal.log import get_logger

shopify_logger = get_logger("shopify")

async def sync_shopify_inventory():
    try:
        shopify_logger.info("Iniciando sincronización con Shopify")
        
        # Obtener datos de Shopify
        inventory_data = await get_shopify_inventory()
        shopify_logger.info(f"Obtenidos {len(inventory_data)} productos de Shopify")
        
        # Procesar datos
        processed_count = await process_inventory_data(inventory_data)
        
        shopify_logger.info(f"Sincronización completada: {processed_count} productos procesados")
        
    except Exception as e:
        shopify_logger.exception("Error durante la sincronización con Shopify")
        raise
```

### 4. Manejo de Errores con Context

```python
from app.internal.log import get_logger

error_logger = get_logger("error_handler")

def handle_user_action(user_id: str, action: str):
    try:
        error_logger.debug(f"Usuario {user_id} ejecutando acción: {action}")
        
        # Lógica de la acción
        result = execute_action(action)
        
        error_logger.info(f"Acción '{action}' completada exitosamente para usuario {user_id}")
        return result
        
    except ValueError as e:
        error_logger.warning(f"Datos inválidos en acción '{action}' para usuario {user_id}: {str(e)}")
        raise
    except Exception as e:
        error_logger.exception(f"Error inesperado en acción '{action}' para usuario {user_id}")
        raise
```

## Configuración de Niveles por Ambiente

### Desarrollo Local
- **Archivo (logs/app.log)**: INFO y superior
- **Consola**: DEBUG y superior (para depuración detallada)

### Producción Azure Container Apps
- **Consola solamente**: INFO y superior (va a logs del contenedor Docker)
- **Sin archivos**: Los logs se manejan por Azure Container Apps
- **Importante**: Los logs de consola son cruciales en contenedores Docker

## Formato de Logs

```
2025-08-06 10:30:15 - CocoSalvajeInventarios - INFO - inventario.py:45 - Iniciando sincronización con Shopify
```

Formato: `TIMESTAMP - LOGGER_NAME - LEVEL - FILE:LINE - MESSAGE`

## Mejores Prácticas

1. **Usa loggers específicos por módulo**:
   ```python
   # En lugar de usar el logger principal para todo
   logger = get_logger("nombre_del_modulo")
   ```

2. **Incluye contexto relevante**:
   ```python
   logger.info(f"Usuario {user_id} realizó acción {action} en {duration:.3f}s")
   ```

3. **Usa niveles apropiados**:
   - `DEBUG`: Información detallada para desarrollo
   - `INFO`: Información general del flujo de la aplicación
   - `WARNING`: Situaciones que requieren atención
   - `ERROR`: Errores que requieren investigación

4. **Loggea excepciones con contexto**:
   ```python
   try:
       process_order(order_id)
   except Exception as e:
       logger.exception(f"Error procesando orden {order_id}")
   ```

5. **Crea instancias de Logger para componentes específicos**:
   ```python
   # Para componentes que necesitan configuración especial
   component_logger = Logger("component_name")
   component_logger.logger.info("Componente inicializado")
   ```

6. **Reutiliza instancias de logger**:
   ```python
   # Al inicio del módulo
   logger = get_logger("mi_modulo")
   
   # Usar en todas las funciones del módulo
   def mi_funcion():
       logger.info("Función ejecutada")
   ```

## Monitoreo

Los logs pueden ser monitoreados usando herramientas como:
- `tail -f logs/app.log` para seguimiento en tiempo real
- `grep ERROR logs/app.log` para buscar errores específicos
- Herramientas de agregación como ELK Stack para análisis avanzado
