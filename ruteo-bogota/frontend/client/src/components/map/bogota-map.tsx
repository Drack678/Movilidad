import { useEffect } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Polyline,
  Popup,
  useMap,
  useMapEvents,
} from "react-leaflet";
import type { LatLngExpression } from "leaflet";
import {
  BOGOTA_CENTER,
  DEFAULT_ZOOM,
  TILE_LIGHT,
  makePin,
  makeDot,
} from "./map-utils";
import type { LatLon, TrafficEdge } from "@/lib/api-types";

export interface RouteLine {
  coordinates: LatLon[];
  color: string;
  weight?: number;
  opacity?: number;
  dashArray?: string;
  label?: string;
}

export interface DotMarker {
  position: LatLon;
  color: string;
  pulse?: boolean;
  popup?: string;
}

interface BogotaMapProps {
  origin?: LatLon | null;
  destination?: LatLon | null;
  routes?: RouteLine[];
  trafficEdges?: TrafficEdge[];
  dots?: DotMarker[];
  onMapClick?: (latlon: LatLon) => void;
  fitTo?: LatLon[] | null;
  className?: string;
  height?: string;
}

function ClickHandler({ onMapClick }: { onMapClick?: (latlon: LatLon) => void }) {
  useMapEvents({
    click(e) {
      onMapClick?.([e.latlng.lat, e.latlng.lng]);
    },
  });
  return null;
}

function FitBounds({ points }: { points?: LatLon[] | null }) {
  const map = useMap();
  useEffect(() => {
    if (points && points.length >= 2) {
      const latlngs = points.map((p) => [p[0], p[1]]) as LatLngExpression[];
      map.fitBounds(latlngs as any, { padding: [48, 48], maxZoom: 15 });
    }
  }, [points, map]);
  return null;
}

// Mantiene el tamaño del mapa correcto cuando el contenedor cambia (tabs, etc.)
function ResizeFix() {
  const map = useMap();
  useEffect(() => {
    const t = setTimeout(() => map.invalidateSize(), 200);
    const onResize = () => map.invalidateSize();
    window.addEventListener("resize", onResize);
    return () => {
      clearTimeout(t);
      window.removeEventListener("resize", onResize);
    };
  }, [map]);
  return null;
}

export function BogotaMap({
  origin,
  destination,
  routes = [],
  trafficEdges = [],
  dots = [],
  onMapClick,
  fitTo,
  className = "",
  height = "100%",
}: BogotaMapProps) {
  return (
    <div className={`overflow-hidden rounded-lg border border-border ${className}`} style={{ height }}>
      <MapContainer
        center={BOGOTA_CENTER}
        zoom={DEFAULT_ZOOM}
        scrollWheelZoom
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer url={TILE_LIGHT.url} attribution={TILE_LIGHT.attribution} />
        <ResizeFix />
        <ClickHandler onMapClick={onMapClick} />
        <FitBounds points={fitTo} />

        {/* Aristas de tráfico (mapa de calor) */}
        {trafficEdges.map((e, i) => (
          <Polyline
            key={`t-${e.u}-${e.v}-${i}`}
            positions={e.coordinates as LatLngExpression[]}
            pathOptions={{ color: e.color, weight: 4, opacity: 0.75 }}
          >
            <Popup>
              <strong>{e.name || "Vía"}</strong>
              <br />
              Nivel de tráfico: {["Muy bajo", "Bajo", "Medio", "Alto", "Muy alto"][e.level] ?? e.level}
            </Popup>
          </Polyline>
        ))}

        {/* Rutas calculadas */}
        {routes.map((r, i) => (
          <Polyline
            key={`r-${i}`}
            positions={r.coordinates as LatLngExpression[]}
            pathOptions={{
              color: r.color,
              weight: r.weight ?? 5,
              opacity: r.opacity ?? 0.9,
              dashArray: r.dashArray,
              lineCap: "round",
              lineJoin: "round",
            }}
          >
            {r.label && <Popup>{r.label}</Popup>}
          </Polyline>
        ))}

        {/* Puntos genéricos (hormigas, nodos explorados) */}
        {dots.map((d, i) => (
          <Marker key={`d-${i}`} position={d.position} icon={makeDot(d.color, d.pulse)}>
            {d.popup && <Popup>{d.popup}</Popup>}
          </Marker>
        ))}

        {origin && (
          <Marker position={origin} icon={makePin("A", "#127d85")}>
            <Popup>Origen</Popup>
          </Marker>
        )}
        {destination && (
          <Marker position={destination} icon={makePin("B", "#b03a52")}>
            <Popup>Destino</Popup>
          </Marker>
        )}
      </MapContainer>
    </div>
  );
}
