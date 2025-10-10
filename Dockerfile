# Dockerfile para API de Inventarios Coco Salvaje

# Usa una imagen base oficial de Python 3.13 slim
FROM python:3.13-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Establece el directorio de trabajo en el contenedor
WORKDIR /app


RUN apt-get update && apt-get install -y \
    python3-dev \
    libpq-dev \
    tzdata && \
    ln -sf /usr/share/zoneinfo/America/Bogota /etc/localtime && \
    echo "America/Bogota" > /etc/timezone && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copia solo los archivos de dependencias primero (para aprovechar cache de Docker)
COPY pyproject.toml ./

# Actualiza pip a la última versión
# RUN pip install --upgrade pip
RUN uv sync

# Instala dependencias usando pip con pyproject.toml
# RUN pip install --no-cache-dir .

# Copia el código de la aplicación
COPY app/ ./app/
COPY app/default_data/ ./app/default_data/
COPY ./reset_admin_pwd.py ./
COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh

# Crea un usuario no-root con UID/GID específicos
RUN adduser --disabled-password --gecos '' --uid 1001 coco && \
    chown -R coco:coco /app

# Cambia al usuario no-root
USER coco

# Expone el puerto 8000
EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]