# Dockerfile para API de Inventarios Coco Salvaje

# Usa una imagen base oficial de Python 3.13 slim
FROM python:3.13-slim-trixie

# Copia uv desde la imagen oficial
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Instala dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    python3-dev \
    libpq-dev \
    tzdata && \
    ln -sf /usr/share/zoneinfo/America/Bogota /etc/localtime && \
    echo "America/Bogota" > /etc/timezone && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Configura uv para no usar entornos virtuales (ya estamos en contenedor)
ENV UV_SYSTEM_PYTHON=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Copia solo los archivos de dependencias primero (para aprovechar cache de Docker)
COPY pyproject.toml uv.lock* ./

# Instala dependencias directamente en el sistema Python
RUN uv sync --frozen --no-dev

# Copia el código de la aplicación
COPY app/ ./app/
COPY app/default_data/ ./app/default_data/
COPY ./reset_admin_pwd.py ./

# Crea un usuario no-root para ejecutar la aplicación
RUN adduser --disabled-password --gecos '' coco && \
    chown -R coco:coco /app

# Cambia al usuario no-root
USER coco

# Expone el puerto 8000
EXPOSE 8000

# Comando para ejecutar la aplicación
CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]