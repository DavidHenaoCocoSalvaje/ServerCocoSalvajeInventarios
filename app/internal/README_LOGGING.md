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
- **Sistema de instancias**: Múltiples loggers reutilizables por nombre
- **Instancia global**: `default_logger` disponible para uso inmediato
- **Rotación de archivos** solo en desarrollo
- **API simplificada**: Solo la clase `Logger` y la instancia `default_logger`

> **Nota importante**: Las variables de Azure Container Apps (`CONTAINER_APP_*`) son proporcionadas automáticamente por Azure cuando tu aplicación se ejecuta en un Container App. No necesitas configurarlas manualmente.

## API del Sistema

### Clase Logger
- `Logger(name)`: Crea o retorna una instancia existente del logger
- `Logger.get_instance(name)`: Método de clase alternativo para obtener instancias
- `logger_instance.logger`: Propiedad que retorna el objeto `logging.Logger` de Python

### Instancia Global
- `default_logger`: Instancia global predefinida con nombre "CocoSalvajeInventarios"

### Comportamiento de Instancias
- Las instancias se **reutilizan automáticamente** por nombre
- `Logger("inventario")` siempre retorna la misma instancia
- Cada logger tiene su propio nombre en los logs para identificación

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
from app.internal.log import Logger
from app.config import config

# Crear una instancia de logger para verificar
logger_instance = Logger("test")

# Verificar usando el config directamente
print(f"Ambiente actual: {config.environment}")
print(f"Es producción: {config.is_production()}")
print(f"Es Azure Container: {config.is_azure_container()}")

# Ver información detallada de Azure Container Apps
azure_info = config.get_azure_container_info()
print(f"Info Azure Container: {azure_info}")
```

## Uso Básico

### Importar el logger

```python
from app.internal.log import Logger, default_logger
```

### Logger principal (instancia global)

```python
# Usar la instancia global predefinida
logger = default_logger.logger
logger.info("Mensaje informativo")
logger.warning("Mensaje de advertencia") 
logger.error("Mensaje de error")
logger.debug("Mensaje de debug")
```

### Crear loggers específicos por módulo

```python
# Logger específico para un módulo (instancias se reutilizan automáticamente)
inventario_logger = Logger("inventario")
inventario_logger.logger.info("Operación de inventario completada")

# Logger para Shopify
shopify_logger = Logger("shopify")
shopify_logger.logger.info("Sincronización con Shopify iniciada")

# Logger para base de datos
db_logger = Logger("database")
db_logger.logger.debug("Query ejecutado correctamente")
```

### Usando el método de clase get_instance

```python
# Método alternativo para obtener instancias
api_logger = Logger.get_instance("api")
api_logger.logger.info("Endpoint API llamado")

# También funciona con el nombre por defecto
main_logger = Logger.get_instance()
main_logger.logger.info("Logger principal via get_instance")
```

### Acceso directo con la propiedad logger

```python
# Todas las instancias tienen la propiedad logger para acceso directo
auth_logger = Logger("auth")
auth_logger.logger.warning("Intento de acceso fallido")

# La propiedad logger retorna el objeto logging.Logger de Python
db_logger = Logger("database")
python_logger = db_logger.logger  # Esto es un logging.Logger estándar
```

## Ejemplos Prácticos

### 1. En un Router de FastAPI

```python
from fastapi import APIRouter, HTTPException
from app.internal.log import Logger
import time

# Logger específico para el router de inventario
logger = Logger("inventario")

router = APIRouter()

@router.get("/productos")
async def get_productos():
    start_time = time.time()
    
    try:
        logger.logger.info("Iniciando consulta de productos")
        
        # Lógica del endpoint
        productos = await consultar_productos()
        
        duration = time.time() - start_time
        logger.logger.info(f"Consulta exitosa: {len(productos)} productos en {duration:.3f}s")
        
        return productos
        
    except Exception as e:
        duration = time.time() - start_time
        logger.logger.exception(f"Error al consultar productos (duración: {duration:.3f}s)")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
```

### 2. En Operaciones de Base de Datos

```python
from app.internal.log import Logger
import time

db_logger = Logger("database")

async def ejecutar_query(query: str, params: dict):
    start_time = time.time()
    
    try:
        db_logger.logger.debug(f"Ejecutando query: {query}")
        
        # Ejecutar query
        result = await database.execute(query, params)
        
        duration = time.time() - start_time
        db_logger.logger.info(f"Query ejecutado exitosamente - Duración: {duration:.3f}s - Filas afectadas: {result.rowcount}")
        
        return result
        
    except Exception as e:
        duration = time.time() - start_time
        db_logger.logger.error(f"Error en query (duración: {duration:.3f}s): {str(e)}")
        raise
```

### 3. En Sincronización con Shopify

```python
from app.internal.log import Logger

shopify_logger = Logger("shopify")

async def sync_shopify_inventory():
    try:
        shopify_logger.logger.info("Iniciando sincronización con Shopify")
        
        # Obtener datos de Shopify
        inventory_data = await get_shopify_inventory()
        shopify_logger.logger.info(f"Obtenidos {len(inventory_data)} productos de Shopify")
        
        # Procesar datos
        processed_count = await process_inventory_data(inventory_data)
        
        shopify_logger.logger.info(f"Sincronización completada: {processed_count} productos procesados")
        
    except Exception as e:
        shopify_logger.logger.exception("Error durante la sincronización con Shopify")
        raise
```

### 4. Manejo de Errores con Context

```python
from app.internal.log import Logger

error_logger = Logger("error_handler")

def handle_user_action(user_id: str, action: str):
    try:
        error_logger.logger.debug(f"Usuario {user_id} ejecutando acción: {action}")
        
        # Lógica de la acción
        result = execute_action(action)
        
        error_logger.logger.info(f"Acción '{action}' completada exitosamente para usuario {user_id}")
        return result
        
    except ValueError as e:
        error_logger.logger.warning(f"Datos inválidos en acción '{action}' para usuario {user_id}: {str(e)}")
        raise
    except Exception as e:
        error_logger.logger.exception(f"Error inesperado en acción '{action}' para usuario {user_id}")
        raise
```

### 5. Usando la Instancia Global Default

```python
from app.internal.log import default_logger

# Usar directamente la instancia global para logging principal
def main_application_function():
    default_logger.logger.info("Aplicación iniciada")
    
    try:
        # Lógica principal
        result = process_main_logic()
        default_logger.logger.info("Procesamiento principal completado")
        return result
    except Exception as e:
        default_logger.logger.exception("Error en lógica principal de la aplicación")
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
   # Crea un logger específico para cada módulo/componente
   logger = Logger("nombre_del_modulo")
   ```

2. **Reutiliza las instancias de Logger**:
   ```python
   # Al inicio del módulo
   logger = Logger("mi_modulo")
   
   # Las instancias se reutilizan automáticamente
   same_logger = Logger("mi_modulo")  # Misma instancia que arriba
   ```

3. **Usa la instancia global para logging general**:
   ```python
   from app.internal.log import default_logger
   
   # Para logging general de la aplicación
   default_logger.logger.info("Aplicación iniciada")
   ```

4. **Incluye contexto relevante**:
   ```python
   logger = Logger("api")
   logger.logger.info(f"Usuario {user_id} realizó acción {action} en {duration:.3f}s")
   ```

5. **Usa niveles apropiados**:
   - `DEBUG`: Información detallada para desarrollo
   - `INFO`: Información general del flujo de la aplicación
   - `WARNING`: Situaciones que requieren atención
   - `ERROR`: Errores que requieren investigación

6. **Loggea excepciones con contexto**:
   ```python
   logger = Logger("error_handler")
   try:
       process_order(order_id)
   except Exception as e:
       logger.logger.exception(f"Error procesando orden {order_id}")
   ```

7. **Métodos de acceso al logger**:
   ```python
   # Método 1: Crear instancia y usar propiedad
   logger_instance = Logger("mi_modulo")
   logger_instance.logger.info("Mensaje")
   
   # Método 2: Usar get_instance
   logger_instance = Logger.get_instance("mi_modulo")
   logger_instance.logger.info("Mensaje")
   
   # Método 3: Asignar para uso posterior
   logger = Logger("mi_modulo").logger
   logger.info("Mensaje")
   ```

8. **Patrón recomendado por módulo**:
   ```python
   # Al inicio de cada archivo .py
   from app.internal.log import Logger
   
   # Crear logger específico del módulo
   _logger = Logger(__name__)  # Usa el nombre del módulo
   
   # Usar en todas las funciones del módulo
   def mi_funcion():
       _logger.logger.info("Función ejecutada")
   ```

## Monitoreo

Los logs pueden ser monitoreados usando herramientas como:
- `tail -f logs/app.log` para seguimiento en tiempo real
- `grep ERROR logs/app.log` para buscar errores específicos
- Herramientas de agregación como ELK Stack para análisis avanzado
