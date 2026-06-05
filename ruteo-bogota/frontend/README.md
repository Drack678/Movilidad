# RutaBogá — Frontend

Interfaz web para la **Aplicación de Optimización de Rutas Urbanas** de Bogotá. Construida con React + Vite + TypeScript + Tailwind CSS + Leaflet, consume el backend FastAPI (OSMnx + ACO) entregado por separado.

## Arquitectura de conexión con el backend

El frontend **nunca** llama directamente a FastAPI. El servidor Express incluido actúa como **proxy**: reenvía todas las peticiones `/api/*` al backend FastAPI. Así el frontend usa siempre rutas relativas `/api/...` (compatibles con el despliegue) y la URL del backend queda centralizada en un solo lugar.

```
Navegador  ──/api/...──►  Express (proxy, puerto 5000)  ──►  FastAPI (puerto 8000)
```

La URL del backend se configura con la variable de entorno `FASTAPI_URL` (por defecto `http://127.0.0.1:8000`). El proxy vive en `server/routes.ts`.

## Requisitos previos

1. **El backend FastAPI debe estar corriendo** antes de arrancar el frontend. Desde la carpeta `backend/`:

   ```bash
   USE_REAL_GRAPH=0 DATABASE_URL="sqlite:///./data/ruteo_bogota.db" \
     uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

   (Usa `USE_REAL_GRAPH=1` para descargar la red vial real de Bogotá con OSMnx; tarda más la primera vez.)

2. Node.js 20+.

## Desarrollo

```bash
npm install
FASTAPI_URL="http://127.0.0.1:8000" npm run dev
```

Abre `http://127.0.0.1:5000`. El servidor de Express (backend-proxy) y Vite (frontend) corren en el mismo puerto.

## Producción

```bash
npm run build
NODE_ENV=production FASTAPI_URL="http://127.0.0.1:8000" node dist/index.cjs
```

## Vistas

| Ruta            | Vista                  | Descripción                                                                 |
| --------------- | ---------------------- | --------------------------------------------------------------------------- |
| `/`             | Planificador           | Selección de origen/destino en el mapa, modo y algoritmo; cálculo de ruta.  |
| `/comparar`     | Comparar algoritmos    | ACO vs Dijkstra vs A* sobre el mismo par origen-destino (tabla + gráfico).   |
| `/trafico`      | Mapa de tráfico        | Mapa de calor de congestión con simulación (estrategia + hora) y leyenda.    |
| `/aco`          | Visualizador ACO       | Reproductor paso a paso de las hormigas y curva de convergencia del costo.   |
| `/analitica`    | Analítica              | KPIs de la red, tiempo medio por hora, distribución y vías más congestionadas. |
| `/ubicaciones`  | Ubicaciones guardadas  | CRUD de lugares frecuentes fijados en el mapa.                               |

## Estructura

```
client/src/
  lib/         api-types.ts (tipos del backend), format.ts, queryClient.ts, utils.ts
  components/  app-shell.tsx, theme-provider.tsx, logo.tsx, shared.tsx
    map/       bogota-map.tsx, map-utils.ts (Leaflet)
  pages/       planner, compare, traffic, aco-viz, analytics, locations
server/        index.ts, routes.ts (proxy → FastAPI), vite.ts, static.ts
```

## Notas

- Mapas con Leaflet + react-leaflet, teselas Carto Voyager (filtro dark-mode aplicado por CSS).
- Gráficos con Recharts. Animaciones con Framer Motion.
- Modo claro/oscuro (sin persistencia en almacenamiento local por restricción del entorno).
