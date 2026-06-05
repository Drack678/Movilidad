import { type ReactNode } from "react";
<<<<<<< HEAD
import { Car, Bike, Footprints, Bus } from "lucide-react";
=======
import { Car, Bike, Footprints } from "lucide-react";
>>>>>>> 0bee57f2e1b8fe42a131df70f129a08fbe5945fa
import type { TransportMode, Algorithm } from "@/lib/api-types";

export function PageHeader({
  title,
  subtitle,
  icon,
  actions,
}: {
  title: string;
  subtitle?: string;
  icon?: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-3 border-b border-border bg-card px-5 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-8">
      <div className="flex items-start gap-3">
        {icon && <div className="mt-0.5 text-primary">{icon}</div>}
        <div>
          <h1 className="font-display text-xl font-bold tracking-tight text-foreground">{title}</h1>
          {subtitle && <p className="mt-0.5 text-sm text-muted-foreground">{subtitle}</p>}
        </div>
      </div>
      {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
    </div>
  );
}

export function StatCard({
  label,
  value,
  hint,
  accent,
  testId,
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  accent?: string;
  testId?: string;
}) {
  return (
    <div
      className="rounded-lg border border-card-border bg-card p-4"
      data-testid={testId}
    >
      <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</div>
      <div
        className="mt-1 font-mono text-lg font-semibold tabular text-foreground"
        style={accent ? { color: accent } : undefined}
      >
        {value}
      </div>
      {hint && <div className="mt-0.5 text-xs text-muted-foreground">{hint}</div>}
    </div>
  );
}

const MODE_META: Record<TransportMode, { label: string; icon: typeof Car }> = {
  car: { label: "Auto", icon: Car },
  bike: { label: "Bici", icon: Bike },
  foot: { label: "A pie", icon: Footprints },
<<<<<<< HEAD
  transmilenio: { label: "TM", icon: Bus },
=======
>>>>>>> 0bee57f2e1b8fe42a131df70f129a08fbe5945fa
};

export function ModeSelector({
  value,
  onChange,
}: {
  value: TransportMode;
  onChange: (m: TransportMode) => void;
}) {
  return (
<<<<<<< HEAD
    <div className="grid grid-cols-4 gap-1.5 rounded-lg border border-border bg-muted/40 p-1">
=======
    <div className="grid grid-cols-3 gap-1.5 rounded-lg border border-border bg-muted/40 p-1">
>>>>>>> 0bee57f2e1b8fe42a131df70f129a08fbe5945fa
      {(Object.keys(MODE_META) as TransportMode[]).map((m) => {
        const { label, icon: Icon } = MODE_META[m];
        const active = value === m;
        return (
          <button
            key={m}
            onClick={() => onChange(m)}
            className={`flex items-center justify-center gap-1.5 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
              active
                ? "bg-primary text-primary-foreground shadow-sm"
                : "text-muted-foreground hover-elevate"
            }`}
            data-testid={`button-mode-${m}`}
          >
            <Icon size={16} /> {label}
          </button>
        );
      })}
    </div>
  );
}

const ALGO_OPTIONS: { value: Algorithm; label: string }[] = [
  { value: "aco", label: "ACO (Hormigas)" },
  { value: "dijkstra", label: "Dijkstra" },
  { value: "astar", label: "A*" },
  { value: "bellman_ford", label: "Bellman-Ford" },
];

export function AlgoSelector({
  value,
  onChange,
}: {
  value: Algorithm;
  onChange: (a: Algorithm) => void;
}) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {ALGO_OPTIONS.map((o) => {
        const active = value === o.value;
        return (
          <button
            key={o.value}
            onClick={() => onChange(o.value)}
            className={`rounded-md border px-3 py-1.5 text-sm font-medium transition-colors ${
              active
                ? "border-primary bg-primary/10 text-primary"
                : "border-border text-muted-foreground hover-elevate"
            }`}
            data-testid={`button-algo-${o.value}`}
          >
            {o.label}
          </button>
        );
      })}
    </div>
  );
}

export function EmptyState({
  icon,
  title,
  message,
}: {
  icon?: ReactNode;
  title: string;
  message: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-border bg-muted/20 px-6 py-12 text-center">
      {icon && <div className="text-muted-foreground/60">{icon}</div>}
      <div>
        <p className="font-medium text-foreground">{title}</p>
        <p className="mt-1 max-w-sm text-sm text-muted-foreground">{message}</p>
      </div>
    </div>
  );
}
