import { type ReactNode, useState } from "react";
import { Link, useLocation } from "wouter";
import { useQuery } from "@tanstack/react-query";
import {
  Map as MapIcon,
  GitCompareArrows,
  Flame,
  Bug,
  BarChart3,
  Bookmark,
  Sun,
  Moon,
  Menu,
  X,
  Github,
} from "lucide-react";
import { Wordmark, Logo } from "./logo";
import { useTheme } from "./theme-provider";
import type { ReadyResponse } from "@/lib/api-types";

const NAV = [
  { href: "/", label: "Planificador", icon: MapIcon, desc: "Calcular ruta óptima" },
  { href: "/comparar", label: "Comparar algoritmos", icon: GitCompareArrows, desc: "ACO vs Dijkstra vs A*" },
  { href: "/trafico", label: "Mapa de tráfico", icon: Flame, desc: "Congestión y simulación" },
  { href: "/aco", label: "Visualizador ACO", icon: Bug, desc: "Hormigas paso a paso" },
  { href: "/analitica", label: "Analítica", icon: BarChart3, desc: "Estadísticas de la red" },
  { href: "/ubicaciones", label: "Ubicaciones", icon: Bookmark, desc: "Lugares guardados" },
];

function StatusPill() {
  const { data, isError, isLoading } = useQuery<ReadyResponse>({
    queryKey: ["/api/ready"],
    refetchInterval: 30000,
  });

  let color = "bg-status-away";
  let label = "Conectando…";
  if (isError) {
    color = "bg-status-busy";
    label = "Backend desconectado";
  } else if (data?.ready) {
    color = "bg-status-online";
    label = `${data.n_nodes.toLocaleString("es-CO")} nodos · ${data.n_edges.toLocaleString("es-CO")} vías`;
  } else if (isLoading) {
    label = "Conectando…";
  }

  return (
    <div
      className="flex items-center gap-2 rounded-md border border-sidebar-border bg-sidebar-accent/40 px-3 py-2"
      data-testid="status-backend"
    >
      <span className={`h-2 w-2 shrink-0 rounded-full ${color}`} />
      <span className="truncate text-xs text-sidebar-foreground/80">{label}</span>
    </div>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const [location] = useLocation();
  const { theme, toggle } = useTheme();
  const [mobileOpen, setMobileOpen] = useState(false);

  const SidebarContent = (
    <div className="flex h-full flex-col bg-sidebar text-sidebar-foreground">
      <div className="flex items-center justify-between px-5 py-5">
        <Link href="/" onClick={() => setMobileOpen(false)}>
          <span className="text-sidebar-foreground" data-testid="link-home-logo">
            <Wordmark />
          </span>
        </Link>
        <button
          className="rounded-md p-1.5 text-sidebar-foreground/70 hover-elevate lg:hidden"
          onClick={() => setMobileOpen(false)}
          aria-label="Cerrar menú"
          data-testid="button-close-menu"
        >
          <X size={20} />
        </button>
      </div>

      <nav className="flex-1 space-y-1 px-3">
        {NAV.map((item) => {
          const active = location === item.href;
          const Icon = item.icon;
          return (
            <Link key={item.href} href={item.href} onClick={() => setMobileOpen(false)}>
              <span
                className={`group flex cursor-pointer items-start gap-3 rounded-md px-3 py-2.5 transition-colors hover-elevate ${
                  active
                    ? "bg-sidebar-primary/15 text-sidebar-foreground"
                    : "text-sidebar-foreground/75"
                }`}
                data-testid={`link-nav-${item.href === "/" ? "home" : item.href.slice(1)}`}
              >
                <Icon
                  size={18}
                  className={`mt-0.5 shrink-0 ${active ? "text-sidebar-primary" : "text-sidebar-foreground/60"}`}
                />
                <span className="min-w-0">
                  <span className="block text-sm font-medium leading-tight">{item.label}</span>
                  <span className="block truncate text-xs text-sidebar-foreground/50">{item.desc}</span>
                </span>
              </span>
            </Link>
          );
        })}
      </nav>

      <div className="space-y-3 px-3 pb-5 pt-3">
        <StatusPill />
        <div className="flex items-center justify-between px-2">
          <span className="text-xs text-sidebar-foreground/45">Bogotá · OSM + ACO</span>
          <button
            onClick={toggle}
            className="rounded-md p-2 text-sidebar-foreground/70 hover-elevate"
            aria-label={theme === "dark" ? "Activar modo claro" : "Activar modo oscuro"}
            data-testid="button-theme-toggle"
          >
            {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="flex h-screen w-full overflow-hidden bg-background">
      {/* Sidebar desktop */}
      <aside className="hidden w-72 shrink-0 border-r border-sidebar-border lg:block">
        {SidebarContent}
      </aside>

      {/* Sidebar móvil */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setMobileOpen(false)}
          />
          <div className="absolute left-0 top-0 h-full w-72 shadow-xl">{SidebarContent}</div>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        {/* Topbar móvil */}
        <header className="flex items-center justify-between border-b border-border bg-card px-4 py-3 lg:hidden">
          <button
            onClick={() => setMobileOpen(true)}
            className="rounded-md p-2 hover-elevate"
            aria-label="Abrir menú"
            data-testid="button-open-menu"
          >
            <Menu size={20} />
          </button>
          <span className="text-foreground">
            <Wordmark />
          </span>
          <button
            onClick={toggle}
            className="rounded-md p-2 hover-elevate"
            aria-label="Cambiar tema"
            data-testid="button-theme-toggle-mobile"
          >
            {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
          </button>
        </header>

        <main className="flex-1 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}
