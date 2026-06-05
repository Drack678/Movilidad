import L from "leaflet";

// Centro de Bogotá (Plaza de Bolívar) y límites del grafo representativo.
export const BOGOTA_CENTER: [number, number] = [4.5981, -74.0758];
export const DEFAULT_ZOOM = 12;
export const BOGOTA_BOUNDS: L.LatLngBoundsExpression = [
  [4.45, -74.22],
  [4.82, -73.98],
];

/** Pin tipo "gota" con etiqueta (origen/destino). */
export function makePin(label: string, color: string): L.DivIcon {
  return L.divIcon({
    className: "",
    html: `<div class="map-pin" style="background:${color}">${label}</div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  });
}

/** Punto pequeño (hormiga / nodo). */
export function makeDot(color: string, pulse = false): L.DivIcon {
  const cls = pulse ? "ant-dot" : "";
  return L.divIcon({
    className: "",
    html: `<div class="${cls}" style="width:12px;height:12px;border-radius:9999px;background:${color};border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.4)"></div>`,
    iconSize: [12, 12],
    iconAnchor: [6, 6],
  });
}

// Tiles claras y oscuras (Carto, gratuitas con atribución).
export const TILE_LIGHT = {
  url: "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
  attribution:
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
};
