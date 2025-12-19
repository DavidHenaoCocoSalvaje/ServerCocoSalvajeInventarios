# Dockerfile para API de Inventarios Coco Salvaje

# Usa una imagen base oficial de Python 3.14 slim
FROM python:3.14-slim-trixie

# Instala uv
COPY --from=ghcr.io/astral-sh/uv /uv /uvx /bin/

# Instala dependencias del sistema
RUN apt-get update && apt-get install -y \
    python3-dev \
    libpq-dev \
    tzdata && \
    ln -sf /usr/share/zoneinfo/America/Bogota /etc/localtime && \
    echo "America/Bogota" > /etc/timezone && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Crea un usuario no-root con UID/GID específicos
RUN adduser --disabled-password --gecos '' --uid 1001 coco

# Copia el código de la aplicación
COPY app/ /home/coco/app/
COPY app/default_data/ /home/coco/app/default_data/

# Copia scripts
COPY ./reset_admin_pwd.py /home/coco/
COPY entrypoint.sh /home/coco/

# Permite ejecutar el entrypoint
RUN chmod +x /home/coco/entrypoint.sh

# Copia pyproject.toml
COPY pyproject.toml /home/coco/

# Establece el directorio de trabajo en el contenedor
WORKDIR /home/coco

# Instala dependencias de Python
RUN uv sync

# Cambia al usuario no-root
RUN chown -R coco:coco /home/coco/
USER coco

# Expone el puerto 8000
EXPOSE 8000

ENTRYPOINT ["/home/coco/entrypoint.sh"]