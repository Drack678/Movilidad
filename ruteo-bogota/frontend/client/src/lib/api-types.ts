/**
 * Tipos TypeScript que reflejan los esquemas del backend FastAPI.
 * Mantienen el frontend fuertemente tipado y alineado con el contrato de la API.
 */

export type TransportMode = "car" | "bike" | "foot" | "transmilenio";
export type Algorithm = "aco" | "dijkstra" | "astar" | "bellman_ford";

export interface AcoParams {
  alpha?: number;
  beta?: number;
  rho?: number;
  q?: number;
  n_ants?: number;
  n_iterations?: number;
  seed?: number | null;
}

export interface RouteRequest {
  origin_lat: number;
  origin_lon: number;
  dest_lat: number;
  dest_lon: number;
  mode: TransportMode;
  algorithm?: Algorithm;
  aco_params?: AcoParams;
}

export type LatLon = [number, number];

export interface RouteResponse {
  algorithm: Algorithm;
  mode: TransportMode;
  found: boolean;
  node_path: number[];
  coordinates: LatLon[];
  total_distance_m: number;
  total_time_s: number;
  total_cost: number;
  runtime_ms: number;
  iterations: number;
  meta: Record<string, any> & {
    history?: AcoIteration[];
    best_cost?: number;
  };
}

export interface AcoIteration {
  iteration: number;
  best_cost: number | null;
  n_successful_ants: number;
  explored_edges: [number, number][];
  best_path: number[];
}

export interface AlgoResult {
  algorithm: Algorithm;
  found: boolean;
  total_distance_m: number;
  total_time_s: number;
  total_cost: number;
  runtime_ms: number;
  iterations: number;
  quality_ratio: number;
}

export interface CompareResponse {
  mode: TransportMode;
  best_algorithm: Algorithm;
  results: AlgoResult[];
  best_route: RouteResponse;
}

export interface TrafficEdge {
  u: number;
  v: number;
  coordinates: [LatLon, LatLon];
  level: number;
  color: string;
  name: string;
}

export interface TrafficLevel {
  level: number;
  label: string;
  color: string;
}

export interface CongestedEdge {
  u: number;
  v: number;
  name: string;
  level: string;
  time_s: number;
}

export interface GraphStats {
  n_nodes: number;
  n_edges: number;
  avg_travel_time_s: number;
  most_congested: CongestedEdge[];
  least_congested: CongestedEdge[];
  traffic_distribution: Record<string, number>;
}

export interface ByHourPoint {
  hour: number;
  avg_travel_time_s: number;
  [key: string]: number;
}

export interface ReadyResponse {
  ready: boolean;
  n_nodes: number;
  n_edges: number;
  city: string;
}

export interface GraphNodes {
  count: number;
  nodes: Record<string, LatLon>;
}

export interface SavedLocation {
  id: number;
  name: string;
  description?: string | null;
  lat: number;
  lon: number;
  category?: string | null;
}

export interface LocationCreate {
  name: string;
  description?: string;
  lat: number;
  lon: number;
  category?: string;
}

// Metadatos de UI para modos y algoritmos.
export const MODE_LABELS: Record<TransportMode, string> = {
  car: "Automóvil",
  bike: "Bicicleta",
  foot: "Peatón",
  transmilenio: "TransMilenio",
};

export const ALGO_LABELS: Record<Algorithm, string> = {
  aco: "Colonia de Hormigas (ACO)",
  dijkstra: "Dijkstra",
  astar: "A*",
  bellman_ford: "Bellman-Ford",
};

export const ALGO_SHORT: Record<Algorithm, string> = {
  aco: "ACO",
  dijkstra: "Dijkstra",
  astar: "A*",
  bellman_ford: "Bellman-Ford",
};
