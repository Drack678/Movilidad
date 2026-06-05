<<<<<<< HEAD
import { useState, useEffect } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
=======
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
>>>>>>> 0bee57f2e1b8fe42a131df70f129a08fbe5945fa
import { apiRequest } from "@/lib/queryClient";
import {
  Map as MapIcon,
  MapPin,
  Navigation,
  Route as RouteIcon,
  Crosshair,
  Loader2,
  Trash2,
  Clock,
  Ruler,
  Gauge,
} from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { PageHeader, StatCard, ModeSelector, AlgoSelector, EmptyState } from "@/components/shared";
import { BogotaMap, type RouteLine } from "@/components/map/bogota-map";
import { useToast } from "@/hooks/use-toast";
import { formatDistance, formatDuration, formatRuntime } from "@/lib/format";
import {
  type LatLon,
  type TransportMode,
  type Algorithm,
  type RouteRequest,
  type RouteResponse,
  ALGO_SHORT,
} from "@/lib/api-types";

const ROUTE_COLOR: Record<Algorithm, string> = {
  aco: "#127d85",
  dijkstra: "#2f6fb0",
  astar: "#d98a1f",
  bellman_ford: "#9b3b6e",
};

type Picking = "origin" | "dest";

<<<<<<< HEAD
// Types for TM network
interface TMStation {
  id: string;
  name: string;
  lat: number;
  lon: number;
}

interface TMLine {
  route_id: string;
  short_name: string;
  color: string;
  stop_sequence: string[];
  geometry: [number, number][];
}

interface TMNetwork {
  nodes: Record<string, TMStation>;
  lines: TMLine[];
}

=======
>>>>>>> 0bee57f2e1b8fe42a131df70f129a08fbe5945fa
export default function PlannerPage() {
  const { toast } = useToast();
  const [origin, setOrigin] = useState<LatLon | null>(null);
  const [dest, setDest] = useState<LatLon | null>(null);
  const [picking, setPicking] = useState<Picking>("origin");
  const [mode, setMode] = useState<TransportMode>("car");
  const [algorithm, setAlgorithm] = useState<Algorithm>("aco");
  const [route, setRoute] = useState<RouteResponse | null>(null);
<<<<<<< HEAD
  const [tmRecommendation, setTmRecommendation] = useState<any>(null);

  // Fetch TM network
  const { data: tmNetwork } = useQuery({
    queryKey: ["tm-network"],
    queryFn: async () => {
      const res = await apiRequest("GET", "/api/transit/gtfs/network");
      return res.json() as TMNetwork;
    },
  });

  const routeMutation = useMutation({
    mutationFn: async (): Promise<any> => {
      if (mode === "transmilenio") {
        // Use TM recommendation endpoint
        const res = await apiRequest(
          "GET",
          `/api/transit/transmilenio/recommendation?origin_lat=${origin![0]}&origin_lon=${origin![1]}&dest_lat=${dest![0]}&dest_lon=${dest![1]}`
        );
        return res.json();
      } else {
        // Original route calculation
        const body: RouteRequest = {
          origin_lat: origin![0],
          origin_lon: origin![1],
          dest_lat: dest![0],
          dest_lon: dest![1],
          mode,
          algorithm,
        };
        const res = await apiRequest("POST", "/api/route", body);
        return res.json();
      }
    },
    onSuccess: (data: any) => {
        if (mode === "transmilenio") {
          setTmRecommendation(data);
          setRoute(null);
        } else {
          setRoute(data);
          setTmRecommendation(null);
          if (!data.found) {
              toast({
                  title: "Sin ruta",
                  description: "No se encontró una ruta entre los puntos seleccionados, pero intentamos usar la mejor opción disponible.",
                  variant: "default",
              });
          }
=======

  const routeMutation = useMutation({
    mutationFn: async (): Promise<RouteResponse> => {
      const body: RouteRequest = {
        origin_lat: origin![0],
        origin_lon: origin![1],
        dest_lat: dest![0],
        dest_lon: dest![1],
        mode,
        algorithm,
      };
      const res = await apiRequest("POST", "/api/route", body);
      return res.json();
    },
    onSuccess: (data: RouteResponse) => {
        setRoute(data);
        if (!data.found) {
            toast({
                title: "Sin ruta",
                description: "No se encontró una ruta entre los puntos seleccionados, pero intentamos usar la mejor opción disponible.",
                variant: "default",
            });
>>>>>>> 0bee57f2e1b8fe42a131df70f129a08fbe5945fa
        }
    },
    onError: (err: Error) => {
      toast({ title: "Error al calcular la ruta", description: err.message, variant: "destructive" });
    },
  });

  function handleMapClick(latlon: LatLon) {
    if (picking === "origin") {
      setOrigin(latlon);
      setPicking("dest");
    } else {
      setDest(latlon);
      setPicking("origin");
    }
    setRoute(null);
  }

  function clearAll() {
    setOrigin(null);
    setDest(null);
    setRoute(null);
    setPicking("origin");
  }

<<<<<<< HEAD
  // Prepare routes for map
  let routes: RouteLine[] = [];
  let fitTo: LatLon[] | null = null;

  if (mode === "transmilenio" && tmRecommendation) {
    // Add TM lines to map
    if (tmNetwork) {
      routes = tmNetwork.lines.map((line) => ({
        coordinates: line.geometry,
        color: line.color,
        weight: 3,
        opacity: 0.6,
        label: line.short_name,
      }));
    }
    // If there's a direct route, highlight it
    if (tmRecommendation.routes && tmRecommendation.routes.length > 0) {
      const direct = tmRecommendation.routes[0];
      if (direct.geometry) {
        routes.push({
          coordinates: direct.geometry,
          color: "#e11d48",
          weight: 6,
          opacity: 0.9,
          label: direct.name,
        });
        fitTo = direct.geometry;
      }
    }
  } else if (route?.found && route.coordinates.length) {
    routes = [{ coordinates: route.coordinates, color: ROUTE_COLOR[algorithm], weight: 6 }];
    fitTo = route.coordinates;
  }

=======
  const routes: RouteLine[] =
    route?.found && route.coordinates.length
      ? [{ coordinates: route.coordinates, color: ROUTE_COLOR[algorithm], weight: 6 }]
      : [];

  const fitTo = route?.found && route.coordinates.length ? route.coordinates : null;
>>>>>>> 0bee57f2e1b8fe42a131df70f129a08fbe5945fa
  const canCalc = origin && dest;

  return (
    <AppShell>
      <PageHeader
        title="Planificador de rutas"
        subtitle="Selecciona origen y destino en el mapa y calcula la ruta óptima"
        icon={<MapIcon size={22} />}
      />
      <div className="grid gap-4 p-4 sm:p-6 lg:grid-cols-[380px_1fr]">
        {/* Panel de control */}
        <div className="space-y-4">
          <div className="rounded-lg border border-card-border bg-card p-4">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-foreground">Puntos del viaje</h2>
              {(origin || dest) && (
                <button
                  onClick={clearAll}
                  className="flex items-center gap-1 rounded-md px-2 py-1 text-xs text-muted-foreground hover-elevate"
                  data-testid="button-clear"
                >
                  <Trash2 size={13} /> Limpiar
                </button>
              )}
            </div>

            <div className="space-y-2">
              <button
                onClick={() => setPicking("origin")}
                className={`flex w-full items-center gap-3 rounded-md border px-3 py-2.5 text-left transition-colors ${
                  picking === "origin" ? "border-primary bg-primary/5" : "border-border hover-elevate"
                }`}
                data-testid="button-pick-origin"
              >
                <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-primary text-xs font-bold text-primary-foreground">
                  A
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block text-xs text-muted-foreground">Origen</span>
                  <span className="block truncate font-mono text-xs text-foreground">
                    {origin ? `${origin[0].toFixed(5)}, ${origin[1].toFixed(5)}` : "Toca el mapa para fijar"}
                  </span>
                </span>
                {picking === "origin" && <Crosshair size={15} className="text-primary" />}
              </button>

              <button
                onClick={() => setPicking("dest")}
                className={`flex w-full items-center gap-3 rounded-md border px-3 py-2.5 text-left transition-colors ${
                  picking === "dest" ? "border-primary bg-primary/5" : "border-border hover-elevate"
                }`}
                data-testid="button-pick-dest"
              >
                <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-destructive text-xs font-bold text-destructive-foreground">
                  B
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block text-xs text-muted-foreground">Destino</span>
                  <span className="block truncate font-mono text-xs text-foreground">
                    {dest ? `${dest[0].toFixed(5)}, ${dest[1].toFixed(5)}` : "Toca el mapa para fijar"}
                  </span>
                </span>
                {picking === "dest" && <Crosshair size={15} className="text-primary" />}
              </button>
            </div>
          </div>

          <div className="rounded-lg border border-card-border bg-card p-4">
            <h2 className="mb-2 text-sm font-semibold text-foreground">Modo de transporte</h2>
            <ModeSelector value={mode} onChange={(m) => { setMode(m); setRoute(null); }} />
            <h2 className="mb-2 mt-4 text-sm font-semibold text-foreground">Algoritmo</h2>
            <AlgoSelector value={algorithm} onChange={(a) => { setAlgorithm(a); setRoute(null); }} />
          </div>

          <button
            onClick={() => routeMutation.mutate()}
            disabled={!canCalc || routeMutation.isPending}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground transition-colors hover-elevate disabled:cursor-not-allowed disabled:opacity-50"
            data-testid="button-calculate-route"
          >
            {routeMutation.isPending ? (
              <>
                <Loader2 size={16} className="animate-spin" /> Calculando…
              </>
            ) : (
              <>
                <Navigation size={16} /> Calcular ruta
              </>
            )}
          </button>

<<<<<<< HEAD
          {mode === "transmilenio" && tmRecommendation ? (
            <div className="space-y-3">
              {tmRecommendation.origin_station && (
                <StatCard
                  label="Estación de origen"
                  value={tmRecommendation.origin_station.name}
                  hint={`a ${tmRecommendation.origin_station.distance_m}m`}
                />
              )}
              {tmRecommendation.destination_station && (
                <StatCard
                  label="Estación de destino"
                  value={tmRecommendation.destination_station.name}
                  hint={`a ${tmRecommendation.destination_station.distance_m}m`}
                />
              )}
              {tmRecommendation.routes && tmRecommendation.routes.length > 0 && (
                <div className="rounded-lg border border-card-border bg-card p-4">
                  <h3 className="text-sm font-semibold text-foreground mb-2">Rutas recomendadas</h3>
                  <div className="space-y-1">
                    {tmRecommendation.routes.map((r: any, i: number) => (
                      <div key={i} className="text-sm text-muted-foreground">
                        <span className="font-medium">{r.name}</span>
                        {r.origin && r.destination && ` — ${r.origin} → ${r.destination}`}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : route?.found ? (
=======
          {route?.found && (
>>>>>>> 0bee57f2e1b8fe42a131df70f129a08fbe5945fa
            <div className="grid grid-cols-2 gap-3" data-testid="route-results">
              <StatCard
                label="Distancia"
                value={formatDistance(route.total_distance_m)}
                testId="stat-distance"
              />
              <StatCard
                label="Tiempo estimado"
                value={formatDuration(route.total_time_s)}
                testId="stat-time"
              />
              <StatCard
                label="Algoritmo"
                value={ALGO_SHORT[route.algorithm]}
                hint={route.iterations ? `${route.iterations} iteraciones` : "óptimo exacto"}
                testId="stat-algo"
              />
              <StatCard
                label="Cómputo"
                value={formatRuntime(route.runtime_ms)}
                hint={`${route.node_path.length} nodos`}
                testId="stat-runtime"
              />
            </div>
<<<<<<< HEAD
          ) : null}
=======
          )}
>>>>>>> 0bee57f2e1b8fe42a131df70f129a08fbe5945fa
        </div>

        {/* Mapa */}
        <div className="min-h-[420px] lg:min-h-0">
          <div className="flex h-full min-h-[480px] flex-col gap-2">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <MapPin size={13} className="text-primary" />
              {canCalc
                ? "Listo para calcular. Toca el mapa para reubicar los puntos."
                : `Toca el mapa para fijar el ${picking === "origin" ? "origen (A)" : "destino (B)"}.`}
            </div>
            <div className="flex-1">
              <BogotaMap
                origin={origin}
                destination={dest}
                routes={routes}
                onMapClick={handleMapClick}
                fitTo={fitTo}
                height="100%"
                className="h-full"
              />
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
