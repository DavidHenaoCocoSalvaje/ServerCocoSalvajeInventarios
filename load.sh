#!/bin/bash

# Colores y Estilos
BOLD="\033[1m"
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
RESET="\033[0m"

# Funciones de logging
log_info() { echo -e "${BLUE}${BOLD}[INFO]${RESET} $1"; }
log_success() { echo -e "${GREEN}${BOLD}[OK]${RESET} $1"; }
log_warn() { echo -e "${YELLOW}${BOLD}[WARN]${RESET} $1"; }
log_error() { echo -e "${RED}${BOLD}[ERROR]${RESET} $1"; }

IMAGE_NAME="integraciones-api"

echo -e "\n${BOLD}🚀 Iniciando ciclo de despliegue para ${YELLOW}${IMAGE_NAME}${RESET}\n"

# 1. Limpieza de contenedores
log_info "Deteniendo y eliminando contenedor ${IMAGE_NAME}..."
if docker stop "$IMAGE_NAME" &>/dev/null; then
    log_success "Contenedor detenido."
else
    log_warn "El contenedor no estaba corriendo o no se pudo detener."
fi

if docker rm "$IMAGE_NAME" &>/dev/null; then
    log_success "Contenedor eliminado."
else
    log_warn "No se requirió eliminar el contenedor."
fi

# 2. Construcción (Build)
log_info "Construyendo imagen ejecutando ./build.sh..."
# Ejecutamos build.sh. Si falla, detenemos el script.
if ./build.sh; then
    log_success "Build completado."
else
    log_error "Falló la ejecución de ./build.sh"
    exit 1
fi

# 3. Cargar Imagen
log_info "Cargando imagen desde build/${IMAGE_NAME}.tar..."
if docker load -i "build/${IMAGE_NAME}.tar"; then
    log_success "Imagen cargada en Docker Engine."
else
    log_error "Error cargando la imagen. Verifica que el archivo build/${IMAGE_NAME}.tar exista."
    exit 1
fi

# 4. Docker Compose Up
log_info "Levantando servicios con docker compose up -d..."
if docker compose up -d; then
    log_success "Servicios levantados."
    echo -e "\n${GREEN}${BOLD}✨ ¡Proceso finalizado exitosamente!${RESET}\n"
else
    log_error "Error al levantar docker compose."
    exit 1
fi