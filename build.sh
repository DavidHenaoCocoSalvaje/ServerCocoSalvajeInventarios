#!/bin/bash
# Este script construye la imagen de Docker y guarda la salida en la carpeta build

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

IMAGE_NAME="integraciones-api:latest"
# Construir la imagen
echo -e "${GREEN}🚀 Construyendo imagen${NC}"
docker build -t "${IMAGE_NAME}" .
echo -e "${YELLOW}🧹 Eliminando imágenes huérfanas...${NC}"
docker image prune -f
docker save "${IMAGE_NAME}" -o "build/${IMAGE_NAME}.tar"
echo -e "${GREEN}✅ Imagen construida y guardada en build/${IMAGE_NAME}.tar${NC}"