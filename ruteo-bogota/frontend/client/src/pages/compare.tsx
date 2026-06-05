import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import {
  GitCompareArrows,
  Loader2,
  Trophy,
  Trash2,
  Crosshair,
  Zap,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RTooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { AppShell } from "@/components/app-shell";
import { PageHeader, ModeSelector, EmptyState } from "@/components/shared";
import { BogotaMap, type RouteLine } from "@/components/map/bogota-map";
import { useToast } from "@/hooks/use-toast";
import { formatDistance, formatDuration, formatRuntime } from "@/lib/format";
import {
  type LatLon,
  type TransportMode,
  type Algorithm,
  type CompareResponse,
  ALGO_SHORT,
} from "@/lib/api-types";

const ALGO_COLOR: Record<string, string> = {
  aco: "#127d85",
  dijkstra: "#2f6fb0",
  astar: "#d98a1f",
  bellman_ford: "#9b3b6e",
};

type Picking = "origin" | "dest";

export default function ComparePage() {
  const { toast } = useToast();
  const [origin, setOrigin] = useState<LatLon | null>([4.55, -74.15]);
  const [dest, setDest] = useState<LatLon | null>([4.72, -74.05]);
  const [picking, setPicking] = useState<Picking>("origin");
  const [mode, setMode] = useState<TransportMode>("car");
  const [data, setData] = useState<CompareResponse | null>(null);

  const mut = useMutation({
    mutationFn: async (): Promise<CompareResponse> => {
      const res = await apiRequest("POST", "/api/route/compare", {
        origin_lat: origin![0],
        origin_lon: origin![1],
        dest_lat: dest![0],
        dest_lon: dest![1],
        mode,
      });
      return res.json();
    },
    onSuccess: setData,
    onError: (err: Error) =>
      toast({ title: "Error al comparar", description: err.message, variant: "destructive" }),
  });

  function handleMapClick(latlon: LatLon) {
    if (picking === "origin") {
      setOrigin(latlon);
      setPicking("dest");
    } else {
      setDest(latlon);
      setPicking("origin");
    }
    setData(null);
  }

  const routes: RouteLine[] =
    data?.best_route?.found && data.best_route.coordinates.length
      ? [
          {
            coordinates: data.best_route.coordinates,
            color: ALGO_COLOR[data.best_algorithm] ?? "#127d85",
            weight: 6,
            label: `Mejor ruta: ${ALGO_SHORT[data.best_algorithm]}`,
          },
        ]
      : [];

  const chartData =
    data?.results
      .filter((r) => r.found)
      .map((r) => ({
        name: ALGO_SHORT[r.algorithm],
        algorithm: r.algorithm,
        tiempo: Math.round(r.total_time_s),
        distancia: Math.round(r.total_distance_m),
        computo: r.runtime_ms,
        calidad: r.quality_ratio,
      })) ?? [];

  return (
    <AppShell>
      <PageHeader
        title="Comparación de algoritmos"
        subtitle="Mismo origen-destino resuelto por ACO, Dijkstra y A* en paralelo"
        icon={<GitCompareArrows size={22} />}
      />
      <div className="space-y-4 p-4 sm:p-6">
        {/* Controles */}
        <div className="flex flex-col gap-4 rounded-lg border border-card-border bg-card p-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="flex flex-1 flex-col gap-3 sm:flex-row sm:items-center">
            <button
              onClick={() => setPicking("origin")}
              className={`flex flex-1 items-center gap-2 rounded-md border px-3 py-2 text-left ${
                picking === "origin" ? "border-primary bg-primary/5" : "border-border hover-elevate"
              }`}
              data-testid="button-pick-origin"
            >
              <span className="grid h-6 w-6 place-items-center rounded-full bg-primary text-xs font-bold text-primary-foreground">A</span>
              <span className="font-mono text-xs text-foreground">
                {origin ? `${origin[0].toFixed(4)}, ${origin[1].toFixed(4)}` : "Origen"}
              </span>
              {picking === "origin" && <Crosshair size={13} className="ml-auto text-primary" />}
            </button>
            <button
              onClick={() => setPicking("dest")}
              className={`flex flex-1 items-center gap-2 rounded-md border px-3 py-2 text-left ${
                picking === "dest" ? "border-primary bg-primary/5" : "border-border hover-elevate"
              }`}
              data-testid="button-pick-dest"
            >
              <span className="grid h-6 w-6 place-items-center rounded-full bg-destructive text-xs font-bold text-destructive-foreground">B</span>
              <span className="font-mono text-xs text-foreground">
                {dest ? `${dest[0].toFixed(4)}, ${dest[1].toFixed(4)}` : "Destino"}
              </span>
              {picking === "dest" && <Crosshair size={13} className="ml-auto text-primary" />}
            </button>
          </div>
          <div className="flex items-end gap-3">
            <div className="w-44">
              <ModeSelector value={mode} onChange={(m) => { setMode(m); setData(null); }} />
            </div>
            <button
              onClick={() => mut.mutate()}
              disabled={!origin || !dest || mut.isPending}
              className="flex items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground hover-elevate disabled:opacity-50"
              data-testid="button-compare"
            >
              {mut.isPending ? <Loader2 size={16} className="animate-spin" /> : <Zap size={16} />}
              Comparar
            </button>
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          {/* Mapa */}
          <div className="h-[420px]">
            <BogotaMap
              origin={origin}
              destination={dest}
              routes={routes}
              onMapClick={handleMapClick}
              fitTo={routes[0]?.coordinates ?? null}
              height="100%"
            />
          </div>

          {/* Resultados */}
          <div className="space-y-4">
            {!data ? (
              <EmptyState
                icon={<GitCompareArrows size={40} />}
                title="Aún sin comparación"
                message="Ajusta los puntos y pulsa Comparar para ver cómo se desempeña cada algoritmo."
              />
            ) : (
              <>
                <div className="flex items-center gap-2 rounded-lg border border-primary/30 bg-primary/5 px-4 py-3">
                  <Trophy size={18} className="text-primary" />
                  <span className="text-sm text-foreground">
                    Mejor resultado:{" "}
                    <strong className="text-primary">{ALGO_SHORT[data.best_algorithm]}</strong>{" "}
                    por menor costo de ruta.
                  </span>
                </div>

                <div className="overflow-hidden rounded-lg border border-card-border">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border bg-muted/40 text-left text-xs uppercase tracking-wide text-muted-foreground">
                        <th className="px-3 py-2 font-medium">Algoritmo</th>
                        <th className="px-3 py-2 text-right font-medium">Distancia</th>
                        <th className="px-3 py-2 text-right font-medium">Tiempo</th>
                        <th className="px-3 py-2 text-right font-medium">Cómputo</th>
                        <th className="px-3 py-2 text-right font-medium">Calidad</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.results.map((r) => (
                        <tr
                          key={r.algorithm}
                          className={`border-b border-border last:border-0 ${
                            r.algorithm === data.best_algorithm ? "bg-primary/5" : ""
                          }`}
                          data-testid={`row-result-${r.algorithm}`}
                        >
                          <td className="px-3 py-2.5">
                            <span className="flex items-center gap-2">
                              <span
                                className="h-2.5 w-2.5 rounded-full"
                                style={{ background: ALGO_COLOR[r.algorithm] }}
                              />
                              <span className="font-medium text-foreground">{ALGO_SHORT[r.algorithm]}</span>
                            </span>
                          </td>
                          <td className="px-3 py-2.5 text-right font-mono tabular text-foreground">
                            {r.found ? formatDistance(r.total_distance_m) : "—"}
                          </td>
                          <td className="px-3 py-2.5 text-right font-mono tabular text-foreground">
                            {r.found ? formatDuration(r.total_time_s) : "—"}
                          </td>
                          <td className="px-3 py-2.5 text-right font-mono tabular text-muted-foreground">
                            {r.found ? formatRuntime(r.runtime_ms) : "—"}
                          </td>
                          <td className="px-3 py-2.5 text-right font-mono tabular text-foreground">
                            {r.found ? `${r.quality_ratio.toFixed(3)}×` : "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="rounded-lg border border-card-border bg-card p-4">
                  <h3 className="mb-3 text-sm font-semibold text-foreground">
                    Tiempo de viaje por algoritmo (s)
                  </h3>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={chartData} margin={{ top: 10, right: 20, bottom: 30, left: 40 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                      <XAxis 
                        dataKey="name" 
                        tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
                        label={{ value: "Algoritmo", position: "insideBottom", offset: -10, fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
                      />
                      <YAxis 
                        tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} 
                        width={56}
                        label={{ value: "Tiempo (segundos)", angle: -90, position: "insideLeft", fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
                      />
                      <RTooltip
                        contentStyle={{
                          background: "hsl(var(--popover))",
                          border: "1px solid hsl(var(--border))",
                          borderRadius: 8,
                          fontSize: 12,
                          color: "hsl(var(--popover-foreground))",
                          boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
                          zIndex: 1000
                        }}
                        labelStyle={{ color: "hsl(var(--popover-foreground))" }}
                        itemStyle={{ color: "hsl(var(--popover-foreground))" }}
                        formatter={(v: number) => [`${v.toLocaleString("es-CO")} s`, "Tiempo"]}
                      />
                      <Bar dataKey="tiempo" radius={[4, 4, 0, 0]}>
                        {chartData.map((d) => (
                          <Cell key={d.algorithm} fill={ALGO_COLOR[d.algorithm]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                  <p className="mt-3 text-xs text-muted-foreground">
                    Dijkstra y A* garantizan el óptimo exacto. El ACO es una metaheurística: su
                    relación de calidad indica cuántas veces el costo de su ruta supera al óptimo.
                  </p>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
