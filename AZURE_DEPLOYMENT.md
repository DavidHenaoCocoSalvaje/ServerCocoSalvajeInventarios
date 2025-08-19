# Despliegue en Azure Container Apps

Este directorio contiene los archivos necesarios para desplegar la API de Inventarios Coco Salvaje en Azure Container Apps.

## Archivos de Despliegue

- `Dockerfile`: Configuración del contenedor optimizada para Azure
- `.dockerignore`: Archivos excluidos del contexto de construcción
- `.env.example`: Ejemplo de variables de entorno necesarias
- `deploy-azure.ps1`: Script de despliegue para PowerShell

## Requisitos Previos

1. **Azure CLI instalado**: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
2. **Docker instalado**: Para pruebas locales (opcional)
3. **Base de datos PostgreSQL**: En Azure Database for PostgreSQL o similar

## Pasos de Despliegue

### 1. Configurar Azure CLI

```powershell
# Iniciar sesión en Azure
az login

# Establecer la suscripción (si tienes múltiples)
az account set --subscription "tu-suscripcion-id"
```

### 2. Configurar Variables de Entorno

Edita el archivo `deploy-azure.ps1` y modifica las variables según tus necesidades:

```powershell
$RESOURCE_GROUP = "rg-cosal-inventarios"
$LOCATION = "East US"  # O tu región preferida
$CONTAINER_APP_ENV = "env-cosal-inventarios"
$CONTAINER_APP_NAME = "app-cosal-inventarios"
```

### 3. Configurar Base de Datos

Crea una base de datos PostgreSQL en Azure:

```powershell
# Crear servidor PostgreSQL
az postgres flexible-server create \
  --resource-group $RESOURCE_GROUP \
  --name "pg-cosal-inventarios" \
  --location $LOCATION \
  --admin-user "cosal_admin" \
  --admin-password "TuContraseñaSegura123!" \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --version 14

# Crear base de datos
az postgres flexible-server db create \
  --resource-group $RESOURCE_GROUP \
  --server-name "pg-cosal-inventarios" \
  --database-name "inventarios_cosal"

# Configurar firewall para Azure Services
az postgres flexible-server firewall-rule create \
  --resource-group $RESOURCE_GROUP \
  --name "pg-cosal-inventarios" \
  --rule-name "AllowAzureServices" \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

### 4. Ejecutar Despliegue

```powershell
# Ejecutar el script de despliegue
.\deploy-azure.ps1
```

### 5. Configurar Variables de Entorno Sensibles

Actualiza las variables de entorno con valores reales:

```powershell
az containerapp update \
  --name "app-cosal-inventarios" \
  --resource-group "rg-cosal-inventarios" \
  --set-env-vars \
    "DB_HOST=pg-cosal-inventarios.postgres.database.azure.com" \
    "DB_PASSWORD=TuContraseñaRealSegura" \
    "SECRET_KEY=TuClaveSecretaJWTMuySegura"
```

## Prueba Local con Docker

Para probar localmente antes del despliegue:

```powershell
# Construir la imagen
docker build -t cosal-inventarios-api .

# Ejecutar localmente
docker run -p 8000:8000 --env-file .env cosal-inventarios-api
```

## Configuración de Dominio Personalizado

Para usar un dominio personalizado:

```powershell
az containerapp hostname add \
  --hostname "api.tudominio.com" \
  --name "app-cosal-inventarios" \
  --resource-group "rg-cosal-inventarios"
```

## Monitoreo y Logs

```powershell
# Ver logs en tiempo real
az containerapp logs show \
  --name "app-cosal-inventarios" \
  --resource-group "rg-cosal-inventarios" \
  --follow

# Ver métricas
az monitor metrics list \
  --resource "/subscriptions/{subscription-id}/resourceGroups/rg-cosal-inventarios/providers/Microsoft.App/containerApps/app-cosal-inventarios"
```

## Escalado Automático

La aplicación está configurada para escalar automáticamente entre 1 y 3 réplicas. Para modificar:

```powershell
az containerapp update \
  --name "app-cosal-inventarios" \
  --resource-group "rg-cosal-inventarios" \
  --min-replicas 2 \
  --max-replicas 5
```

## Costos Estimados

- Container App: ~$15-30/mes (dependiendo del uso)
- PostgreSQL Flexible Server (Standard_B1ms): ~$20-25/mes
- **Total estimado**: $35-55/mes

## Troubleshooting

### Problema: La aplicación no inicia

1. Verificar logs: `az containerapp logs show`
2. Verificar variables de entorno
3. Verificar conectividad a la base de datos

### Problema: Error de conexión a base de datos

1. Verificar reglas de firewall de PostgreSQL
2. Verificar string de conexión
3. Verificar credenciales

### Problema: Problemas de rendimiento

1. Aumentar CPU/memoria en Container App
2. Verificar consultas de base de datos
3. Implementar cache si es necesario

## Seguridad

- Las variables de entorno sensibles se almacenan de forma segura en Azure
- La aplicación usa HTTPS por defecto
- La base de datos requiere SSL
- Se recomienda usar Azure Key Vault para secretos adicionales
