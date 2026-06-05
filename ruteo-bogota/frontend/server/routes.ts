import type { Express, Request, Response } from "express";
import type { Server } from "node:http";

/**
 * El backend real de la aplicación es un servicio Python (FastAPI) que vive en
 * un proceso aparte. Este servidor Express NO implementa lógica de negocio:
 * únicamente actúa como *proxy* reenviando todas las peticiones `/api/*` al
 * backend FastAPI. Así el frontend siempre llama a rutas relativas `/api/...`
 * (compatibles con el reescritor de URLs del despliegue) y la conexión con el
 * backend entregado queda centralizada en un solo lugar.
 *
 * La URL del backend se configura con la variable de entorno `FASTAPI_URL`
 * (por defecto http://127.0.0.1:8000).
 */
const FASTAPI_URL = (process.env.FASTAPI_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

export async function registerRoutes(
  httpServer: Server,
  app: Express,
): Promise<Server> {
  // Usamos app.use con prefijo en lugar de app.all("/api/*"): Express 5
  // (path-to-regexp v8) ya no admite el comodín `*` sin nombre. Este middleware
  // captura cualquier método y cualquier subruta bajo /api.
  app.use("/api", async (req: Request, res: Response) => {
    const targetUrl = `${FASTAPI_URL}${req.originalUrl}`;
    try {
      const hasBody = req.method !== "GET" && req.method !== "HEAD";
      const upstream = await fetch(targetUrl, {
        method: req.method,
        headers: { "Content-Type": "application/json" },
        body: hasBody && req.body ? JSON.stringify(req.body) : undefined,
      });

      const contentType = upstream.headers.get("content-type") || "application/json";
      res.status(upstream.status);
      res.setHeader("Content-Type", contentType);
      const text = await upstream.text();
      res.send(text);
    } catch (err) {
      console.error(`[proxy] Error al contactar el backend FastAPI en ${targetUrl}:`, err);
      res.status(502).json({
        message:
          "No se pudo contactar el backend FastAPI. Verifica que el servicio Python esté en ejecución (uvicorn app.main:app --port 8000).",
      });
    }
  });

  return httpServer;
}
