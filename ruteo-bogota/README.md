# RutaBogá — Optimización de Rutas Urbanas

Aplicación web completa para la **optimización de rutas urbanas en Bogotá** mediante el algoritmo de **Colonia de Hormigas (ACO)**, comparado con Dijkstra, A\* y Bellman-Ford sobre la red vial real (OSMnx).

El proyecto está dividido en dos servicios independientes que se comunican por HTTP:

```
┌──────────────────────────────┐        ┌──────────────────────────────┐
│  FRONTEND                     │        │  BACKEND                      │
│  React + Vite + Leaflet       │        │  FastAPI + OSMnx + NetworkX   │
│  Express como proxy /api/*    │ ─────► │  ACO / Dijkstra / A* / B-F    │
│  Puerto 5000                  │        │  Puerto 8000                  │
└──────────────────────────────┘        └──────────────────────────────┘
                                                  │
                                                  ▼
                                          SQLite (por defecto)
                                          o PostgreSQL + PostGIS
```

El frontend **nunca** llama directamente a FastAPI: su servidor Express reenvía todas las peticiones `/api/*` al backend (variable `FASTAPI_URL`). Así el frontend usa siempre rutas relativas y la conexión queda centralizada.

---

## Estructura del proyecto

```
ruteo-bogota/
├── README.md                  ← este archivo
├── docker-compose.yml         ← orquesta db + backend + frontend
├── .gitignore
│
├── backend/                   ← API FastAPI (Python)
│   ├── app/
│   │   ├── main.py            ← punto de entrada, registra routers
│   │   ├── api/routes/        ← health, locations, routing, traffic, analytics, graph
│   │   ├── algorithms/        ← ACO, Dijkstra, A*, Bellman-Ford
│   │   ├── graph/             ← carga de red vial (OSMnx / grafo representativo)
│   │   ├── traffic/           ← simulación de congestión
│   │   ├── models/            ← esquemas Pydantic
│   │   ├── core/              ← configuración
│   │   └── database/          ← persistencia de ubicaciones
│   ├── data/                  ← grafo de ejemplo + base SQLite
│   ├── database/init.sql      ← esquema PostgreSQL/PostGIS
│   ├── scripts/ · tests/
│   ├── Dockerfile
│   ├── requirements.txt · requirements-dev.txt · pyproject.toml
│   └── README.md              ← documentación detallada del backend
│
└── frontend/                  ← interfaz React (TypeScript)
    ├── client/src/
    │   ├── pages/             ← planner, compare, traffic, aco-viz, analytics, locations
    │   ├── components/        ← app-shell, mapa (Leaflet), componentes compartidos
    │   └── lib/               ← tipos de la API, formato, cliente HTTP
    ├── server/                ← Express (proxy → FastAPI)
    ├── Dockerfile
    ├── package.json
    └── README.md              ← documentación detallada del frontend
```

---

## Puesta en marcha

### Opción A — Docker (todo el stack)

Requiere Docker y Docker Compose. Levanta base de datos, backend y frontend:

```bash
docker compose up --build
```

- Frontend: http://localhost:5000
- API (docs): http://localhost:8000/docs

### Opción B — Manual (desarrollo)

**1. Backend** (terminal 1):

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
USE_REAL_GRAPH=0 DATABASE_URL="sqlite:///./data/ruteo_bogota.db" \
  uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- `USE_REAL_GRAPH=0` → arranca con el grafo representativo (rápido).
- `USE_REAL_GRAPH=1` → descarga la red vial real de Bogotá con OSMnx (lento la primera vez, luego cachea).

**2. Frontend** (terminal 2, con el backend ya corriendo):

```bash
cd frontend
npm install
FASTAPI_URL="http://127.0.0.1:8000" npm run dev
```

Abre http://127.0.0.1:5000

---

## Vistas de la aplicación

| Ruta           | Vista                 | Descripción                                                                    |
| -------------- | --------------------- | ------------------------------------------------------------------------------ |
| `/`            | Planificador          | Selección de origen/destino en el mapa, modo y algoritmo; cálculo de ruta.     |
| `/comparar`    | Comparar algoritmos   | ACO vs Dijkstra vs A\* sobre el mismo par origen-destino (tabla + gráfico).     |
| `/trafico`     | Mapa de tráfico       | Mapa de calor de congestión con simulación (estrategia + hora) y leyenda.       |
| `/aco`         | Visualizador ACO      | Reproductor paso a paso de las hormigas y curva de convergencia del costo.      |
| `/analitica`   | Analítica             | KPIs de la red, tiempo medio por hora, distribución y vías más congestionadas.  |
| `/ubicaciones` | Ubicaciones guardadas | CRUD de lugares frecuentes fijados en el mapa.                                  |

---

## Endpoints principales del backend (prefijo `/api`)

- `GET /api/health`, `GET /api/ready` — estado y métricas de la red.
- `POST /api/route` — calcula una ruta (modo + algoritmo).
- `POST /api/route/compare` — compara algoritmos sobre el mismo trayecto.
- `POST /api/route/aco/steps` — historial de iteraciones del ACO (para el visualizador).
- `POST|GET /api/locations`, `GET|DELETE /api/locations/{id}` — ubicaciones guardadas.
- `POST /api/traffic/generate`, `GET /api/traffic/heatmap`, `GET /api/traffic/levels` — tráfico.
- `GET /api/analytics/stats`, `GET /api/analytics/by-hour` — analítica.
- `GET /api/graph/nodes` — nodos de la red (mapeo de IDs a coordenadas para el visualizador ACO).

La documentación interactiva (Swagger) está disponible en `http://localhost:8000/docs`.

---

## Tecnologías

- **Backend:** Python, FastAPI, OSMnx, NetworkX, SQLAlchemy, Pydantic.
- **Frontend:** React, TypeScript, Vite, Tailwind CSS, Leaflet, Recharts, Framer Motion, TanStack Query.
- **Infraestructura:** Docker, Docker Compose, PostgreSQL + PostGIS (opcional; SQLite por defecto).

Consulta los `README.md` dentro de `backend/` y `frontend/` para detalles específicos de cada servicio.
