import { useState, useEffect, useRef, useMemo } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import {
  Bug,
  Loader2,
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Crosshair,
  Settings2,
} from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RTooltip, ResponsiveContainer } from "recharts";
import { AppShell } from "@/components/app-shell";
import { PageHeader, StatCard, EmptyState } from "@/components/shared";
import { BogotaMap, type RouteLine, type DotMarker } from "@/components/map/bogota-map";
import { useToast } from "@/hooks/use-toast";
import { formatRuntime } from "@/lib/format";
import type { LatLon, RouteResponse, GraphNodes, AcoIteration } from "@/lib/api-types";

type Picking = "origin" | "dest";

export default function AcoVizPage() {
  const { toast } = useToast();
  const [origin, setOrigin] = useState<LatLon | null>([4.55, -74.15]);
  const [dest, setDest] = useState<LatLon | null>([4.72, -74.05]);
  const [picking, setPicking] = useState<Picking>("origin");
  const [nAnts, setNAnts] = useState(20);
  const [nIter, setNIter] = useState(30);
  const [result, setResult] = useState<RouteResponse | null>(null);
  const [step, setStep] = useState(0);
  const [playing, setPlaying] = useState(false);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  const nodesQ = useQuery<GraphNodes>({
    queryKey: ["/api/graph/nodes"],
    staleTime: Infinity,
  });
  const nodeMap = nodesQ.data?.nodes ?? {};

  const run = useMutation({
    mutationFn: async (): Promise<RouteResponse> => {
      const res = await apiRequest("POST", "/api/route/aco/steps", {
        origin_lat: origin![0],
        origin_lon: origin![1],
        dest_lat: dest![0],
        dest_lon: dest![1],
        mode: "car",
        aco_params: { n_ants: nAnts, n_iterations: nIter, seed: 42 },
      });
      return res.json();
    },
    onSuccess: (data) => {
      setResult(data);
      setStep(0);
      setPlaying(true);
    },
    onError: (err: Error) =>
      toast({ title: "Error en la simulación", description: err.message, variant: "destructive" }),
  });

  const history: AcoIteration[] = result?.meta?.history ?? [];

  // Animación automática
  useEffect(() => {
    if (playing && history.length > 0) {
      timer.current = setInterval(() => {
        setStep((s) => {
          if (s >= history.length - 1) {
            setPlaying(false);
            return s;
          }
          return s + 1;
        });
      }, 700);
    }
    return () => {
      if (timer.current) clearInterval(timer.current);
    };
  }, [playing, history.length]);

  const current = history[step];

  function nodesToCoords(ids: number[]): LatLon[] {
    return ids.map((id) => nodeMap[String(id)]).filter(Boolean) as LatLon[];
  }

  // Aristas exploradas en esta iteración (gris claro)
  const exploredLines: RouteLine[] = useMemo(() => {
    if (!current) return [];
    return current.explored_edges
      .map(([u, v]) => {
        const a = nodeMap[String(u)];
        const b = nodeMap[String(v)];
        if (!a || !b) return null;
        return { coordinates: [a, b], color: "#9aa6b2", weight: 1.5, opacity: 0.35 } as RouteLine;
      })
      .filter(Boolean) as RouteLine[];
  }, [current, nodeMap]);

  // Mejor camino hasta esta iteración (acento)
  const bestLine: RouteLine[] = useMemo(() => {
    if (!current?.best_path?.length) return [];
    const coords = nodesToCoords(current.best_path);
    return coords.length >= 2 ? [{ coordinates: coords, color: "#127d85", weight: 5, opacity: 0.95 }] : [];
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [current, nodeMap]);

  // "Hormigas" = extremos de algunas aristas exploradas, con pulso
  const antDots: DotMarker[] = useMemo(() => {
    if (!current) return [];
    return current.explored_edges.slice(0, 18).map(([, v]) => {
      const p = nodeMap[String(v)];
      return p ? { position: p, color: "#d98a1f", pulse: true } : null;
    }).filter(Boolean) as DotMarker[];
  }, [current, nodeMap]);

  const convergenceData = history.map((h) => ({
    iter: h.iteration,
    costo: h.best_cost ? Math.round(h.best_cost) : null,
  }));

  function handleMapClick(latlon: LatLon) {
    if (picking === "origin") {
      setOrigin(latlon);
      setPicking("dest");
    } else {
      setDest(latlon);
      setPicking("origin");
    }
    setResult(null);
    setPlaying(false);
  }

  return (
    <AppShell>
      <PageHeader
        title="Visualizador del ACO"
        subtitle="Observa cómo la colonia de hormigas explora la red y converge a la mejor ruta"
        icon={<Bug size={22} />}
      />
      <div className="grid gap-4 p-4 sm:p-6 lg:grid-cols-[340px_1fr]">
        {/* Controles */}
        <div className="space-y-4">
          <div className="rounded-lg border border-card-border bg-card p-4">
            <h2 className="mb-3 text-sm font-semibold text-foreground">Puntos del viaje</h2>
            <div className="space-y-2">
              <button
                onClick={() => setPicking("origin")}
                className={`flex w-full items-center gap-2 rounded-md border px-3 py-2 text-left ${picking === "origin" ? "border-primary bg-primary/5" : "border-border hover-elevate"}`}
                data-testid="button-pick-origin"
              >
                <span className="grid h-6 w-6 place-items-center rounded-full bg-primary text-xs font-bold text-primary-foreground">A</span>
                <span className="font-mono text-xs text-foreground">{origin ? `${origin[0].toFixed(4)}, ${origin[1].toFixed(4)}` : "Origen"}</span>
                {picking === "origin" && <Crosshair size={13} className="ml-auto text-primary" />}
              </button>
              <button
                onClick={() => setPicking("dest")}
                className={`flex w-full items-center gap-2 rounded-md border px-3 py-2 text-left ${picking === "dest" ? "border-primary bg-primary/5" : "border-border hover-elevate"}`}
                data-testid="button-pick-dest"
              >
                <span className="grid h-6 w-6 place-items-center rounded-full bg-destructive text-xs font-bold text-destructive-foreground">B</span>
                <span className="font-mono text-xs text-foreground">{dest ? `${dest[0].toFixed(4)}, ${dest[1].toFixed(4)}` : "Destino"}</span>
                {picking === "dest" && <Crosshair size={13} className="ml-auto text-primary" />}
              </button>
            </div>
          </div>

          <div className="rounded-lg border border-card-border bg-card p-4">
            <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-foreground">
              <Settings2 size={15} className="text-primary" /> Parámetros del ACO
            </h2>
            <label className="mb-1.5 flex items-center justify-between text-xs font-medium text-muted-foreground">
              <span>Hormigas</span>
              <span className="font-mono text-foreground">{nAnts}</span>
            </label>
            <input type="range" min={5} max={40} value={nAnts} onChange={(e) => setNAnts(Number(e.target.value))} className="mb-3 w-full accent-primary" data-testid="input-ants" />
            <label className="mb-1.5 flex items-center justify-between text-xs font-medium text-muted-foreground">
              <span>Iteraciones</span>
              <span className="font-mono text-foreground">{nIter}</span>
            </label>
            <input type="range" min={5} max={60} value={nIter} onChange={(e) => setNIter(Number(e.target.value))} className="mb-3 w-full accent-primary" data-testid="input-iterations" />
            <button
              onClick={() => run.mutate()}
              disabled={!origin || !dest || run.isPending || nodesQ.isLoading}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground hover-elevate disabled:opacity-50"
              data-testid="button-run-aco"
            >
              {run.isPending ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />}
              Ejecutar simulación
            </button>
          </div>

          {result && (
            <div className="grid grid-cols-2 gap-3">
              <StatCard label="Iteración" value={`${current?.iteration ?? 0} / ${history.length - 1}`} testId="stat-iteration" />
              <StatCard label="Hormigas exitosas" value={current?.n_successful_ants ?? 0} testId="stat-ants" />
              <StatCard label="Mejor costo" value={current?.best_cost ? Math.round(current.best_cost).toLocaleString("es-CO") : "—"} hint="costo de ruta" testId="stat-cost" />
              <StatCard label="Cómputo total" value={formatRuntime(result.runtime_ms)} testId="stat-runtime" />
            </div>
          )}
        </div>

        {/* Mapa + animación */}
        <div className="space-y-3">
          <div className="h-[460px]">
            <BogotaMap
              origin={origin}
              destination={dest}
              routes={[...exploredLines, ...bestLine]}
              dots={antDots}
              onMapClick={handleMapClick}
              fitTo={result?.found ? result.coordinates : null}
              height="100%"
            />
          </div>

          {result && history.length > 0 && (
            <>
              {/* Controles de reproducción */}
              <div className="flex items-center gap-3 rounded-lg border border-card-border bg-card px-4 py-2.5">
                <button onClick={() => { setStep(0); setPlaying(false); }} className="rounded-md p-1.5 hover-elevate" data-testid="button-step-start" aria-label="Inicio">
                  <SkipBack size={16} />
                </button>
                <button onClick={() => setPlaying((p) => !p)} className="rounded-md bg-primary p-2 text-primary-foreground hover-elevate" data-testid="button-play-pause" aria-label="Reproducir/Pausar">
                  {playing ? <Pause size={16} /> : <Play size={16} />}
                </button>
                <button onClick={() => { setStep((s) => Math.min(history.length - 1, s + 1)); setPlaying(false); }} className="rounded-md p-1.5 hover-elevate" data-testid="button-step-next" aria-label="Siguiente">
                  <SkipForward size={16} />
                </button>
                <input
                  type="range"
                  min={0}
                  max={history.length - 1}
                  value={step}
                  onChange={(e) => { setStep(Number(e.target.value)); setPlaying(false); }}
                  className="flex-1 accent-primary"
                  data-testid="input-step"
                />
                <span className="w-16 text-right font-mono text-xs text-muted-foreground">
                  {step}/{history.length - 1}
                </span>
              </div>

              {/* Curva de convergencia */}
              <div className="rounded-lg border border-card-border bg-card p-4">
                <h3 className="mb-2 text-sm font-semibold text-foreground">Convergencia del mejor costo</h3>
                <ResponsiveContainer width="100%" height={180}>
                  <LineChart data={convergenceData} margin={{ top: 10, right: 20, bottom: 20, left: 40 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                    <XAxis 
                      dataKey="iter" 
                      tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} 
                      label={{ value: "Iteración", position: "insideBottom", offset: -5, fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
                    />
                    <YAxis 
                      tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} 
                      width={56} 
                      domain={["auto", "auto"]}
                      label={{ value: "Costo (unidades)", angle: -90, position: "insideLeft", fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
                    />
                    <RTooltip
                      contentStyle={{ 
                        background: "hsl(var(--popover))", 
                        border: "1px solid hsl(var(--border))", 
                        borderRadius: 8, 
                        fontSize: 12, 
                        color: "hsl(var(--popover-foreground))",
                        boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)"
                      }}
                      formatter={(v: number) => [v?.toLocaleString("es-CO"), "Mejor costo"]}
                      labelFormatter={(l: number) => `Iteración ${l}`}
                    />
                    <Line type="monotone" dataKey="costo" stroke="hsl(var(--primary))" strokeWidth={2} dot={false} connectNulls />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </>
          )}

          {!result && (
            <EmptyState
              icon={<Bug size={40} />}
              title="Simulación lista"
              message="Configura los parámetros y ejecuta para ver a las hormigas (puntos ámbar) explorar la red mientras el mejor camino (línea teal) se refina por iteración."
            />
          )}
        </div>
      </div>
    </AppShell>
  );
}
