#!/bin/bash
set -e

echo "🏗️ Ejecutando inicialización de base de datos..."
uv run python -m app.entrypoint

echo "🚀 Iniciando aplicación FastAPI..."
exec uv run fastapi run app/main.py --host 0.0.0.0 --port 8000 --workers 4
