# ---------------------------------------------------------------------------
# Imagen del frontend de "RutaBogá".
#
# Construye el cliente React (Vite) y el servidor Express (proxy → FastAPI)
# en una sola imagen. El Express resultante sirve los estáticos compilados y
# reenvía /api/* al backend indicado por la variable FASTAPI_URL.
# ---------------------------------------------------------------------------

# --- Etapa de build ---
FROM node:20-slim AS build
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# --- Etapa de runtime ---
FROM node:20-slim AS runtime
WORKDIR /app
ENV NODE_ENV=production

# Solo dependencias de producción.
COPY package*.json ./
RUN npm ci --omit=dev

# Artefactos compilados (cliente + servidor).
COPY --from=build /app/dist ./dist

EXPOSE 5000
# FASTAPI_URL se inyecta por docker-compose (http://backend:8000).
CMD ["node", "dist/index.cjs"]
