#!/bin/bash
# Este script construye la imagen de Docker y guarda la salida en la carpeta build

# Obtener la rama actual
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")

# Determinar el archivo .env y tag según la rama
case "$BRANCH" in
    "staging")
        ENV_FILE=".env.staging"
        IMAGE_TAG="staging"
        HOST_PORT="8001"
        ;;
    "development"|"develop")
        ENV_FILE=".env.development"
        IMAGE_TAG="development"
        HOST_PORT="8002"
        ;;
    "main"|"master"|"production")
        ENV_FILE=".env"
        IMAGE_TAG="latest"
        HOST_PORT="8000"
        ;;
    *)
        ENV_FILE=".env"
        IMAGE_TAG="$BRANCH"
        HOST_PORT="8003"
        ;;
esac

echo "🚀 Construyendo imagen para rama: $BRANCH"
echo "📄 Usando archivo: $ENV_FILE"
echo "🏷️  Tag de imagen: $IMAGE_TAG"
echo "🔌 Puerto del host: $HOST_PORT"

# Verificar que existe el archivo .env
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: No se encontró $ENV_FILE"
    exit 1
fi

# Exportar variables de entorno para docker-compose
export ENV_FILE="$ENV_FILE"
export IMAGE_TAG="$IMAGE_TAG"
export HOST_PORT="$HOST_PORT"

# Construir la imagen
docker-compose build

# Guardar la imagen en la carpeta build
IMAGE_NAME="coco-salvaje-inventarios:$IMAGE_TAG"
echo "💾 Guardando imagen en build/"
docker save "$IMAGE_NAME" -o "build/coco-salvaje-inventarios-$IMAGE_TAG.tar"

echo "✅ Imagen construida y guardada en build/coco-salvaje-inventarios-$IMAGE_TAG.tar"