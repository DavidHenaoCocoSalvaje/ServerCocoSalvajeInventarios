# Dockerfile para API de Inventarios Coco Salvaje

# Usa una imagen base oficial de Python 3.13 slim
FROM python:3.13-slim-trixie

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

# Actualiza pip a la última versión
RUN pip install --upgrade pip

# Copia solo los archivos de dependencias primero (para aprovechar cache de Docker)
COPY pyproject.toml ./

# Instala dependencias usando pip con pyproject.toml
RUN pip install --no-cache-dir .

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