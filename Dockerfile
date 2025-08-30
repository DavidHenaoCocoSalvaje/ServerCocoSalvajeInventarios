# Dockerfile para API de Inventarios Coco Salvaje

# Usa una imagen base oficial de Python 3.13 slim bookworm
FROM python:3.13-slim-bookworm

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Instala dependencias del sistema necesarias para psycopg y otras librerías
RUN apt-get update && apt-get install -y \
    python3-dev \
    libpq-dev \
    tzdata && \
    ln -sf /usr/share/zoneinfo/America/Bogota /etc/localtime && \
    echo "America/Bogota" > /etc/timezone && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copia el archivo de requisitos primero para aprovechar el cache de Docker
COPY requirements.txt .

# Instala las dependencias de Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia el código de la aplicación
COPY app/ ./app/
COPY app/default_data/ ./app/default_data/
COPY ./reset_admin_pwd.py ./

# Crea un usuario no-root para ejecutar la aplicación (buena práctica de seguridad)
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app

# Cambia al usuario no-root
USER appuser

# Expone el puerto 8000
EXPOSE 8000

# Comando para ejecutar la aplicación
# Usando fastapi run (comando oficial de la documentación)
# Con 2 workers para aprovechar mejor los recursos del VPS
CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
