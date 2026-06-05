import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { BarChart3, Loader2, TrendingUp, Network, Timer, AlertTriangle } from "lucide-react";
import {
  AreaChart,
  Area,
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
import { PageHeader, StatCard } from "@/components/shared";
import { formatDuration, formatNumber } from "@/lib/format";
import type { GraphStats, ByHourPoint } from "@/lib/api-types";

const LEVEL_COLOR: Record<string, string> = {
  "Muy bajo": "#2ecc71",
  Bajo: "#a3e635",
  Medio: "#f1c40f",
  Alto: "#e67e22",
  "Muy alto": "#7b1e3a",
};

export default function AnalyticsPage() {
  const stats = useQuery<GraphStats>({ queryKey: ["/api/analytics/stats"] });
  const byHour = useQuery<ByHourPoint[]>({ queryKey: ["/api/analytics/by-hour"] });

  const dist = stats.data
    ? Object.entries(stats.data.traffic_distribution).map(([label, count]) => ({
        label,
        count,
        color: LEVEL_COLOR[label] ?? "#888",
      }))
    : [];

  const hourData =
    byHour.data?.map((h) => ({
      hora: `${String(h.hour).padStart(2, "0")}h`,
      tiempo: Math.round(h.avg_travel_time_s),
    })) ?? [];

  return (
    <AppShell>
      <PageHeader
        title="Analítica de la red"
        subtitle="Estadísticas del grafo vial y patrones de congestión"
        icon={<BarChart3 size={22} />}
      />
      <div className="space-y-5 p-4 sm:p-6">
        {stats.isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="animate-spin text-muted-foreground" />
          </div>
        ) : (
          <>
            {/* KPIs */}
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
              <StatCard label="Nodos" value={formatNumber(stats.data!.n_nodes)} hint="intersecciones" testId="kpi-nodes" />
              <StatCard label="Vías (aristas)" value={formatNumber(stats.data!.n_edges)} hint="segmentos dirigidos" testId="kpi-edges" />
              <StatCard label="Tiempo medio" value={formatDuration(stats.data!.avg_travel_time_s)} hint="por vía" testId="kpi-avg-time" />
              <StatCard
                label="Vías congestionadas"
                value={formatNumber((stats.data!.traffic_distribution["Muy alto"] ?? 0) + (stats.data!.traffic_distribution["Alto"] ?? 0))}
                hint="nivel alto / muy alto"
                accent="#e67e22"
                testId="kpi-congested"
              />
            </div>

            <div className="grid gap-4 lg:grid-cols-2">
              {/* Tiempo por hora */}
              <div className="rounded-lg border border-card-border bg-card p-4">
                <h3 className="mb-1 flex items-center gap-2 text-sm font-semibold text-foreground">
                  <TrendingUp size={15} className="text-primary" /> Tiempo medio de viaje por hora
                </h3>
                <p className="mb-3 text-xs text-muted-foreground">Patrón diario de congestión (horas pico visibles)</p>
                <ResponsiveContainer width="100%" height={240}>
                  <AreaChart data={hourData} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
                    <defs>
                      <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity={0.35} />
                        <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity={0.02} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                    <XAxis dataKey="hora" tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} interval={2} />
                    <YAxis tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} width={44} />
                    <RTooltip
                      contentStyle={{ background: "hsl(var(--popover))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 12, color: "hsl(var(--popover-foreground))" }}
                      formatter={(v: number) => [`${v} s`, "Tiempo medio"]}
                    />
                    <Area type="monotone" dataKey="tiempo" stroke="hsl(var(--primary))" strokeWidth={2} fill="url(#grad)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              {/* Distribución de niveles */}
              <div className="rounded-lg border border-card-border bg-card p-4">
                <h3 className="mb-1 flex items-center gap-2 text-sm font-semibold text-foreground">
                  <Network size={15} className="text-primary" /> Distribución por nivel de tráfico
                </h3>
                <p className="mb-3 text-xs text-muted-foreground">Cantidad de vías en cada nivel de congestión actual</p>
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={dist} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                    <XAxis dataKey="label" tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} />
                    <YAxis tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} width={48} />
                    <RTooltip
                      contentStyle={{ background: "hsl(var(--popover))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 12, color: "hsl(var(--popover-foreground))" }}
                      formatter={(v: number) => [formatNumber(v), "Vías"]}
                    />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {dist.map((d) => (
                        <Cell key={d.label} fill={d.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Vías más congestionadas */}
            <div className="rounded-lg border border-card-border bg-card p-4">
              <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-foreground">
                <AlertTriangle size={15} className="text-chart-4" /> Vías más congestionadas
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-muted-foreground">
                      <th className="px-3 py-2 font-medium">Vía</th>
                      <th className="px-3 py-2 font-medium">Nivel</th>
                      <th className="px-3 py-2 text-right font-medium">Tiempo de cruce</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats.data!.most_congested.slice(0, 8).map((e, i) => (
                      <tr key={`${e.u}-${e.v}-${i}`} className="border-b border-border last:border-0" data-testid={`row-congested-${i}`}>
                        <td className="px-3 py-2 text-foreground">{e.name || `Vía ${e.u}→${e.v}`}</td>
                        <td className="px-3 py-2">
                          <span className="inline-flex items-center gap-1.5">
                            <span className="h-2.5 w-2.5 rounded-full" style={{ background: LEVEL_COLOR[e.level] ?? "#888" }} />
                            <span className="text-foreground">{e.level}</span>
                          </span>
                        </td>
                        <td className="px-3 py-2 text-right font-mono tabular text-foreground">{formatDuration(e.time_s)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}
