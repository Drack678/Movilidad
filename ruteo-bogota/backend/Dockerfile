# ---------------------------------------------------------------------------
# Imagen del backend "Ruteo Bogotá"
#
# Incluye la pila geoespacial completa (OSMnx, GeoPandas, GDAL) para poder
# descargar la red vial real de Bogotá desde OpenStreetMap.
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS base

# Dependencias del sistema requeridas por GeoPandas/Shapely/OSMnx (GDAL/GEOS/PROJ).
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libgdal-dev \
        gdal-bin \
        libgeos-dev \
        libproj-dev \
        proj-data \
        proj-bin \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Instalar dependencias primero para aprovechar la caché de capas.
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copiar el código de la aplicación.
COPY . .

# Generar el grafo representativo como respaldo (no requiere red).
RUN python -m scripts.generate_sample_graph || true

EXPOSE 8000

# USE_REAL_GRAPH=1 intenta descargar la red real al arrancar; ponlo en 0 para
# arrancar de inmediato con el grafo representativo.
ENV USE_REAL_GRAPH=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
