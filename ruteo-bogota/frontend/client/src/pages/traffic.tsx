import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { Flame, Loader2, RefreshCw, Clock, Sparkles, Construction } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/shared";
import { BogotaMap } from "@/components/map/bogota-map";
import { useToast } from "@/hooks/use-toast";
import type { TrafficEdge, TrafficLevel } from "@/lib/api-types";

type Strategy = "time_of_day" | "rush_hour" | "random";

const STRATEGY_LABEL: Record<Strategy, string> = {
  time_of_day: "Por hora del día",
  rush_hour: "Hora pico",
  random: "Aleatorio",
};

export default function TrafficPage() {
  const { toast } = useToast();
  const [strategy, setStrategy] = useState<Strategy>("time_of_day");
  const [hour, setHour] = useState(8);
  const [limit, setLimit] = useState(400);

  const heatmap = useQuery<TrafficEdge[]>({
    queryKey: ["/api/traffic/heatmap", limit],
    queryFn: async () => {
      const res = await apiRequest("GET", `/api/traffic/heatmap?limit=${limit}`);
      return res.json();
    },
  });

  const levels = useQuery<TrafficLevel[]>({ queryKey: ["/api/traffic/levels"] });

  const generate = useMutation({
    mutationFn: async () => {
      const res = await apiRequest("POST", "/api/traffic/generate", {
        strategy,
        hour: strategy === "time_of_day" ? hour : undefined,
      });
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/traffic/heatmap"] });
      queryClient.invalidateQueries({ queryKey: ["/api/analytics/stats"] });
      toast({ title: "Tráfico regenerado", description: `Estrategia: ${STRATEGY_LABEL[strategy]}` });
    },
    onError: (err: Error) =>
      toast({ title: "Error", description: err.message, variant: "destructive" }),
  });

  return (
    <AppShell>
      <PageHeader
        title="Mapa de calor de tráfico"
        subtitle="Niveles de congestión simulados sobre la red vial de Bogotá"
        icon={<Flame size={22} />}
        actions={
          <button
            onClick={() => heatmap.refetch()}
            className="flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-sm hover-elevate"
            data-testid="button-refresh-heatmap"
          >
            <RefreshCw size={14} /> Refrescar
          </button>
        }
      />
      <div className="grid gap-4 p-4 sm:p-6 lg:grid-cols-[320px_1fr]">
        {/* Panel de simulación */}
        <div className="space-y-4">
          <div className="rounded-lg border border-card-border bg-card p-4">
            <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-foreground">
              <Sparkles size={15} className="text-primary" /> Simular tráfico
            </h2>
            <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Estrategia</label>
            <div className="mb-3 grid gap-1.5">
              {(Object.keys(STRATEGY_LABEL) as Strategy[]).map((s) => (
                <button
                  key={s}
                  onClick={() => setStrategy(s)}
                  className={`rounded-md border px-3 py-2 text-left text-sm transition-colors ${
                    strategy === s ? "border-primary bg-primary/5 text-foreground" : "border-border text-muted-foreground hover-elevate"
                  }`}
                  data-testid={`button-strategy-${s}`}
                >
                  {STRATEGY_LABEL[s]}
                </button>
              ))}
            </div>

            {strategy === "time_of_day" && (
              <div className="mb-3">
                <label className="mb-1.5 flex items-center justify-between text-xs font-medium text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Clock size={12} /> Hora del día
                  </span>
                  <span className="font-mono text-foreground">{String(hour).padStart(2, "0")}:00</span>
                </label>
                <input
                  type="range"
                  min={0}
                  max={23}
                  value={hour}
                  onChange={(e) => setHour(Number(e.target.value))}
                  className="w-full accent-primary"
                  data-testid="input-hour"
                />
              </div>
            )}

            <button
              onClick={() => generate.mutate()}
              disabled={generate.isPending}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground hover-elevate disabled:opacity-50"
              data-testid="button-generate-traffic"
            >
              {generate.isPending ? <Loader2 size={16} className="animate-spin" /> : <RefreshCw size={16} />}
              Generar tráfico
            </button>
          </div>

          {/* Densidad mostrada */}
          <div className="rounded-lg border border-card-border bg-card p-4">
            <label className="mb-1.5 flex items-center justify-between text-xs font-medium text-muted-foreground">
              <span>Vías mostradas</span>
              <span className="font-mono text-foreground">{limit}</span>
            </label>
            <input
              type="range"
              min={100}
              max={1924}
              step={100}
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              className="w-full accent-primary"
              data-testid="input-limit"
            />
          </div>

          {/* Leyenda */}
          <div className="rounded-lg border border-card-border bg-card p-4">
            <h3 className="mb-2 text-sm font-semibold text-foreground">Niveles de congestión</h3>
            <div className="space-y-1.5">
              {levels.data?.map((l) => (
                <div key={l.level} className="flex items-center gap-2 text-sm" data-testid={`legend-${l.level}`}>
                  <span className="h-3 w-6 rounded" style={{ background: l.color }} />
                  <span className="text-foreground">{l.label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Mapa */}
        <div className="h-[560px]">
          {heatmap.isLoading ? (
            <div className="flex h-full items-center justify-center rounded-lg border border-border bg-muted/20">
              <Loader2 className="animate-spin text-muted-foreground" />
            </div>
          ) : (
            <BogotaMap trafficEdges={heatmap.data ?? []} height="100%" />
          )}
        </div>
      </div>
    </AppShell>
  );
}
