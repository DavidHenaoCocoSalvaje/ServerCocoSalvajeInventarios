# Dockerfile para API de Inventarios Coco Salvaje
# Optimizado para Azure Container Apps

# Usa una imagen base oficial de Python 3.13 slim bookworm
FROM python:3.13-slim-bookworm

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Instala dependencias del sistema necesarias para psycopg y otras librerías
RUN apt-get update && apt-get install -y \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia el archivo de requisitos primero para aprovechar el cache de Docker
COPY requirements.txt .

# Instala las dependencias de Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia el código de la aplicación
COPY app/ ./app/
COPY default_data/ ./default_data/

# Crea un usuario no-root para ejecutar la aplicación (buena práctica de seguridad)
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app

# Cambia al usuario no-root
USER appuser

# Expone el puerto 8000 (puerto estándar para Azure Container Apps)
EXPOSE 8000

# Variables de entorno por defecto (pueden ser sobrescritas en Azure)
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Comando para ejecutar la aplicación
# Usando uvicorn con configuración optimizada para producción
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
