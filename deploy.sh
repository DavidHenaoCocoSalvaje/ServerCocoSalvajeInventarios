#!/bin/bash

# Este script carga la nueva imagen, y reinicia el contenedor

set -e

# Obtener la rama actual
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "staging")

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# hacer build de la imagen
./build.sh

echo -e "${YELLOW}🚀 Iniciando despliegue para rama: $BRANCH${NC}"

# Verificar que existe la imagen construida
if [ "$BRANCH" = "main" ]; then
    IMAGE_FILE="build/coco-salvaje-integraciones-api-latest.tar"
else
    IMAGE_FILE="build/coco-salvaje-integraciones-api-$BRANCH.tar"
fi
if [ ! -f "$IMAGE_FILE" ]; then
    echo -e "${RED}❌ Error: No se encontró la imagen $IMAGE_FILE${NC}"
    echo -e "${YELLOW}💡 Ejecuta primero: ./build.sh${NC}"
    exit 1
fi

echo -e "${YELLOW}📦 Imagen encontrada: $IMAGE_FILE${NC}"

# Verificar que existe el archivo de inventario
if [ ! -f "ansible/inventory.yml" ]; then
    echo -e "${RED}❌ Error: No se encontró ansible/inventory.yml${NC}"
    exit 1
fi

# Ejecutar el playbook de Ansible
echo -e "${YELLOW}🎭 Ejecutando playbook de Ansible...${NC}"
cd ansible

ansible-playbook \
    -i inventory.yml \
    playbook.yml \
    -e "git_branch=$BRANCH" \
    --ssh-common-args='-o StrictHostKeyChecking=no'

cd ..

echo -e "${GREEN}✅ Despliegue completado para rama: $BRANCH${NC}"

# Mostrar información útil
case "$BRANCH" in
    "staging")
        PORT="8001"
        ;;
    "development"|"develop")
        PORT="8002"
        ;;
    "main"|"master"|"production")
        PORT="8000"
        ;;
    *)
        PORT="8003"
        ;;
esac

echo -e "${GREEN}🌐 URL del servicio: http://cocosalvajeapps.com:$PORT${NC}"
echo -e "${GREEN}📋 Para ver logs: ssh coco@cocosalvajeapps.com 'docker logs coco-salvaje-integraciones-api-app'${NC}"


