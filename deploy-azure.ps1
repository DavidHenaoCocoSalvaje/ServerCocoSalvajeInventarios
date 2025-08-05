# Script de despliegue para Azure Container Apps
# Ejecuta estos comandos en Azure CLI

# 1. Variables de configuración (modifica según tus necesidades)
$RESOURCE_GROUP = "rg-cosal-inventarios"
$LOCATION = "East US"
$CONTAINER_APP_ENV = "env-cosal-inventarios"
$CONTAINER_APP_NAME = "app-cosal-inventarios"
$CONTAINER_REGISTRY = "acrcosal"  # Opcional: si usas Azure Container Registry
$IMAGE_NAME = "cosal-inventarios-api"
$IMAGE_TAG = "latest"

# 2. Crear grupo de recursos
az group create --name $RESOURCE_GROUP --location $LOCATION

# 3. Crear el entorno de Container Apps
az containerapp env create `
  --name $CONTAINER_APP_ENV `
  --resource-group $RESOURCE_GROUP `
  --location $LOCATION

# 4. Crear la aplicación de contenedor
az containerapp create `
  --name $CONTAINER_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --environment $CONTAINER_APP_ENV `
  --image "mcr.microsoft.com/devcontainers/python:3.11" `
  --target-port 8000 `
  --ingress external `
  --min-replicas 1 `
  --max-replicas 3 `
  --cpu 0.5 `
  --memory 1Gi

# 5. Configurar variables de entorno (IMPORTANTE: Configura estos valores)
az containerapp update `
  --name $CONTAINER_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --set-env-vars `
    "DB_HOST=tu-servidor.postgres.database.azure.com" `
    "DB_PORT=5432" `
    "DB_USER=tu_usuario" `
    "DB_PASSWORD=tu_contraseña" `
    "DB_NAME=inventarios_cosal" `
    "SECRET_KEY=tu_clave_secreta_muy_segura" `
    "LOCAL_TIMEZONE=America/Bogota" `
    "ALGORITHM=HS256" `
    "ACCESS_TOKEN_EXPIRE_MINUTES=30"

# 6. Si usas Azure Container Registry, construye y sube la imagen
# az acr build --registry $CONTAINER_REGISTRY --image $IMAGE_NAME:$IMAGE_TAG .

# 7. Actualizar la aplicación con tu imagen personalizada
# az containerapp update `
#   --name $CONTAINER_APP_NAME `
#   --resource-group $RESOURCE_GROUP `
#   --image "$CONTAINER_REGISTRY.azurecr.io/$IMAGE_NAME:$IMAGE_TAG"

Write-Host "Despliegue completado. La aplicación estará disponible en la URL proporcionada por Azure Container Apps."
