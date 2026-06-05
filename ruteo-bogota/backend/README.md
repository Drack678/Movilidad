# Ruteo Bogotá — Backend

Backend de un sistema inteligente de **optimización de rutas urbanas** para Bogotá.
Calcula rutas óptimas con el algoritmo de **Optimización por Colonia de Hormigas
(Ant Colony Optimization, ACO)** —implementado desde cero— y las compara contra
**Dijkstra**, **A\*** y **Bellman-Ford**, sobre la red vial real de
**OpenStreetMap** (vía OSMnx + NetworkX). Incluye un **motor de simulación de
tráfico**, **perfiles de transporte** (auto, bici, peatón), **mapa de calor** de
congestión y **analítica** para un dashboard.

> Proyecto académico — Universidad Distrital Francisco José de Caldas.

---

## Tabla de contenido

- [Arquitectura](#arquitectura)
- [Requisitos](#requisitos)
- [Puesta en marcha rápida (sin OSMnx)](#puesta-en-marcha-rápida-sin-osmnx)
- [Con la red vial real de Bogotá (OSMnx)](#con-la-red-vial-real-de-bogotá-osmnx)
- [Con Docker (API + PostGIS)](#con-docker-api--postgis)
- [Referencia de la API](#referencia-de-la-api)
- [El algoritmo ACO en detalle](#el-algoritmo-aco-en-detalle)
- [Modos de transporte](#modos-de-transporte)
- [Simulación de tráfico](#simulación-de-tráfico)
- [Tests](#tests)
- [Mapeo con la especificación](#mapeo-con-la-especificación)

---

## Arquitectura

```
backend/
├── app/
│   ├── api/                # API REST (FastAPI)
│   │   ├── routes/         # health, locations, routing, traffic, analytics
│   │   └── state.py        # estado en memoria (grafo + tráfico)
│   ├── algorithms/         # ACO, Dijkstra, A*, Bellman-Ford + comparación
│   │   ├── aco.py
│   │   ├── dijkstra.py
│   │   ├── astar.py
│   │   ├── bellman_ford.py
│   │   ├── base.py         # interfaz común RouteAlgorithm
│   │   └── comparison.py
│   ├── graph/              # construcción y gestión del grafo vial
│   │   ├── road_graph.py   # RoadGraph (DiGraph de NetworkX)
│   │   ├── osm_builder.py  # descarga real con OSMnx
│   │   ├── cost_models.py  # costos por modo de transporte
│   │   └── loader.py       # carga con respaldo (real -> representativo)
│   ├── traffic/            # motor de simulación de tráfico
│   │   └── engine.py
│   ├── models/             # enums, tipos del dominio y esquemas Pydantic
│   ├── database/           # ORM SQLAlchemy + PostGIS (ubicaciones)
│   └── core/               # configuración
├── database/init.sql       # esquema PostgreSQL + PostGIS
├── scripts/                # generación / descarga de grafos
├── tests/                  # pytest (algoritmos, grafo, tráfico, API)
├── Dockerfile
├── requirements.txt        # pila completa (con OSMnx)
└── requirements-dev.txt    # pila mínima (sin OSMnx) para dev/CI
```

Principios de diseño:

- **Independencia de OSMnx**: solo `osm_builder.py` lo importa. El resto del
  sistema opera sobre `RoadGraph`, así que funciona con la red real o con un
  grafo representativo.
- **Algoritmos intercambiables**: todos heredan de `RouteAlgorithm` y exponen
  `solve(origin, dest, mode)`, lo que permite compararlos sin tocar la API.
- **El modo de transporte define el costo**, no el algoritmo. Cambiar de modo
  cambia la ruta óptima sin modificar ACO/Dijkstra/A\*.

---

## Requisitos

- Python 3.11+ (probado en 3.12).
- Para la red real: dependencias del sistema de GDAL/GEOS/PROJ (las trae el
  `Dockerfile`).
- PostgreSQL + PostGIS opcional (si no está disponible, se usa SQLite local).

---

## Puesta en marcha rápida (sin OSMnx)

Ideal para desarrollar o evaluar los algoritmos de inmediato. Usa un grafo
**representativo** de Bogotá (malla de calles con avenidas y ciclorrutas).

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

# Generar el grafo representativo (data/bogota_graph.json)
python -m scripts.generate_sample_graph

# Arrancar la API con el grafo representativo
USE_REAL_GRAPH=0 uvicorn app.main:app --reload
```

Abre la documentación interactiva en **http://localhost:8000/docs**.

---

## Con la red vial real de Bogotá (OSMnx)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # incluye osmnx, geopandas, shapely...

# Descargar y cachear la red real (puede tardar varios minutos)
python -m scripts.build_graph            # red para automóvil (drive)
# python -m scripts.build_graph --type all   # toda la red

# Arrancar la API usando la red real
USE_REAL_GRAPH=1 uvicorn app.main:app --reload
```

El grafo se cachea en `data/bogota_graph.graphml`; los siguientes arranques lo
cargan desde la caché.

---

## Con Docker (API + PostGIS)

Desde la raíz del proyecto:

```bash
docker compose up --build
```

Esto levanta PostgreSQL+PostGIS y la API en **http://localhost:8000**. Por
defecto arranca con el grafo representativo (`USE_REAL_GRAPH=0`); cámbialo a
`1` en `docker-compose.yml` para descargar la red real.

---

## Referencia de la API

Prefijo base: `/api`. Documentación OpenAPI en `/docs` y `/redoc`.

| Método | Ruta                     | Descripción                                            |
| ------ | ------------------------ | ------------------------------------------------------ |
| GET    | `/api/health`            | Estado del servicio.                                   |
| GET    | `/api/ready`             | Indica si el grafo está cargado (nodos/aristas).       |
| POST   | `/api/locations`         | Crear ubicación guardada.                              |
| GET    | `/api/locations`         | Listar ubicaciones.                                    |
| GET    | `/api/locations/{id}`    | Obtener una ubicación.                                 |
| DELETE | `/api/locations/{id}`    | Eliminar una ubicación.                                |
| POST   | `/api/route`             | Calcular una ruta (algoritmo y modo elegibles).        |
| POST   | `/api/route/compare`     | Comparar ACO vs Dijkstra vs A\*.                       |
| POST   | `/api/route/aco/steps`   | ACO con historial por iteración (visualización).       |
| POST   | `/api/traffic/generate`  | Regenerar tráfico (random / time_of_day / rush_hour).  |
| POST   | `/api/traffic/incident`  | Simular accidente o cierre de vía.                     |
| GET    | `/api/traffic/heatmap`   | Estado de tráfico por arista (con colores).            |
| GET    | `/api/traffic/levels`    | Leyenda de niveles y colores.                          |
| GET    | `/api/analytics/stats`   | Estadísticas del grafo y la congestión (dashboard).    |
| GET    | `/api/analytics/by-hour` | Tiempo medio de viaje simulado por hora (0-23).        |

### Ejemplo: comparar algoritmos

```bash
curl -X POST http://localhost:8000/api/route/compare \
  -H "Content-Type: application/json" \
  -d '{
    "origin_lat": 4.52, "origin_lon": -74.17,
    "dest_lat": 4.72,  "dest_lon": -74.05,
    "mode": "car", "algorithm": "aco",
    "aco_params": {"alpha":1.0,"beta":3.0,"rho":0.5,"q":100,"n_ants":20,"n_iterations":40,"seed":7}
  }'
```

Respuesta (resumen): para cada algoritmo se devuelve `total_distance_m`,
`total_time_s`, `total_cost`, `runtime_ms`, `iterations` y `quality_ratio`
(1.0 = mejor solución encontrada), más la `best_route` lista para dibujar.

---

## El algoritmo ACO en detalle

Archivo: `app/algorithms/aco.py`. Implementación **desde cero** que cumple:

- **Inicialización de feromonas** uniforme en todas las aristas (`tau0 = 1`).
- **Heurística por distancia/costo**: `eta_ij = 1 / costo_ij` (vías más baratas
  son más deseables).
- **Probabilidad de transición**:
  `p(i,j) = (tau_ij^alpha · eta_ij^beta) / Σ_k (tau_ik^alpha · eta_ik^beta)`.
- **Selección estocástica** de caminos por ruleta sobre los vecinos no visitados.
- **Evaporación**: `tau ← (1 - rho) · tau` tras cada iteración.
- **Actualización/depósito**: cada hormiga añade `Q / costo_camino` a sus aristas
  (los caminos más cortos refuerzan más).
- **Parámetros configurables**: `alpha`, `beta`, `rho`, `q`, `n_ants`,
  `n_iterations`, `seed` (reproducibilidad).
- **Sesgo direccional opcional** (`goal_bias`): favorece vecinos que acercan al
  destino para acelerar la convergencia (ponlo en `0` para un ACO "puro").
- **Historial por iteración** (`record_history=True`): mejor costo, aristas
  exploradas y mejor camino por iteración, para la **visualización educativa**
  del movimiento de las hormigas.

> Nota académica: el ACO es una **metaheurística** estocástica; encuentra muy
> buenas rutas pero no garantiza el óptimo. Dijkstra y A\* sí lo garantizan (con
> costos no negativos) y sirven como referencia de calidad en la comparación.

---

## Modos de transporte

Archivo: `app/graph/cost_models.py`. Cada modo construye un **costo distinto**
por arista a partir de los mismos atributos físicos:

- **Automóvil** (`car`): minimiza el **tiempo** afectado por la velocidad de la
  vía y el **estado del tráfico**.
- **Bicicleta** (`bike`): bonifica **ciclorrutas/vías secundarias**, penaliza
  **autopistas/vías rápidas**.
- **Peatón** (`foot`): bonifica **andenes/senderos**, penaliza **grandes
  avenidas** e intersecciones peligrosas, y prácticamente prohíbe autopistas.

---

## Simulación de tráfico

Archivo: `app/traffic/engine.py`. Cada vía tiene un nivel dinámico
(Muy bajo → Muy alto) que afecta el tiempo y el costo:

- `generate_random`: nivel aleatorio (con sesgo en arterias).
- `generate_time_of_day(hour)`: nivel según la franja horaria (horas pico
  6-9 y 16-19).
- `generate_rush_hour`: satura las arterias.
- `simulate_accident(u, v)` / `simulate_closure(u, v)`: eventos puntuales
  (los cierres persisten al regenerar el tráfico global).

Colores del mapa de calor: verde → amarillo → naranja → rojo → **vinotinto**
(congestión crítica).

---

## Tests

```bash
cd backend
source .venv/bin/activate
USE_REAL_GRAPH=0 pytest -q
```

Cubren: optimalidad de Dijkstra/A\*/Bellman-Ford, validez y reproducibilidad del
ACO, comparación de algoritmos, efectos del tráfico, costos por modo,
persistencia JSON del grafo y todos los endpoints de la API.

---

## Mapeo con la especificación

| Requisito del enunciado                       | Dónde está                                          |
| --------------------------------------------- | --------------------------------------------------- |
| Grafo vial real con OSMnx + NetworkX          | `graph/osm_builder.py`, `graph/road_graph.py`       |
| ACO desde cero (feromonas, evaporación, etc.) | `algorithms/aco.py`                                 |
| Dijkstra y A\* + comparación                  | `algorithms/{dijkstra,astar}.py`, `comparison.py`   |
| Bellman-Ford                                  | `algorithms/bellman_ford.py`                        |
| Tres modos de transporte                      | `graph/cost_models.py`                              |
| Motor de simulación de tráfico                | `traffic/engine.py`                                 |
| Mapa de calor (colores por nivel)             | `models/enums.py` (TrafficLevel), `routes/traffic`  |
| Dashboard de analítica                        | `routes/analytics.py`                               |
| Visualización del algoritmo (por iteración)   | `algorithms/aco.py` (history), `routes/routing.py`  |
| Ubicaciones guardadas (PostgreSQL/PostGIS)    | `database/*`, `database/init.sql`                   |
| API REST + tipado + documentación + tests     | `app/api/*`, docstrings, `tests/*`                  |
| Docker + escalable a otras ciudades           | `Dockerfile`, `docker-compose.yml`, `CITY_NAME`     |
```
