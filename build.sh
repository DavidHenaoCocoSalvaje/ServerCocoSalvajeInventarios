#!/bin/bash
# Este script construye la imagen de Docker y guarda la salida en la carpeta build

# Obtener la rama actual
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")

# Determinar el archivo .env y tag según la rama
case "$BRANCH" in
    "staging")
        ENV_FILE=".env.staging"
        IMAGE_TAG="staging"
        ;;
    "development"|"develop")
        ENV_FILE=".env"
        IMAGE_TAG="development"
        ;;
    "main"|"master"|"production")
        ENV_FILE=".env.production"
        IMAGE_TAG="latest"
        ;;
    *)
        ENV_FILE=".env"
        IMAGE_TAG="$BRANCH"
        ;;
esac

echo "🚀 Construyendo imagen para rama: $BRANCH"
echo "📄 Usando archivo: $ENV_FILE"
echo "🏷️  Tag de imagen: $IMAGE_TAG"

# Verificar que existe el archivo .env
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: No se encontró $ENV_FILE"
    exit 1
fi

# Construir la imagen
docker build -t "integraciones-api:$IMAGE_TAG" .
# Limipiar imagenes
echo "🧹 Eliminando imágenes huérfanas..."
docker image prune -f

# Guardar la imagen en la carpeta build
IMAGE_NAME="integraciones-api:$IMAGE_TAG"
echo "💾 Guardando imagen en build/"
docker save "$IMAGE_NAME" -o "build/integraciones-api-$IMAGE_TAG.tar"

echo "✅ Imagen construida y guardada en build/integraciones-api-$IMAGE_TAG.tar"