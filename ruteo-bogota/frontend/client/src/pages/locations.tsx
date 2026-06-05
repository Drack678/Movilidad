import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { apiRequest, queryClient } from "@/lib/queryClient";
import {
  MapPin,
  Plus,
  Trash2,
  Crosshair,
  Loader2,
  Bookmark,
  Tag,
} from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { PageHeader, EmptyState } from "@/components/shared";
import { BogotaMap, type DotMarker } from "@/components/map/bogota-map";
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import {
  type LatLon,
  type SavedLocation,
  type LocationCreate,
} from "@/lib/api-types";

const CATEGORIES = [
  { value: "casa", label: "Casa" },
  { value: "trabajo", label: "Trabajo" },
  { value: "estudio", label: "Estudio" },
  { value: "ocio", label: "Ocio" },
  { value: "otro", label: "Otro" },
];

const CATEGORY_COLOR: Record<string, string> = {
  casa: "#127d85",
  trabajo: "#2f6fb0",
  estudio: "#d98a1f",
  ocio: "#9b3b6e",
  otro: "#64748b",
};

function categoryLabel(value?: string | null) {
  if (!value) return "Sin categoría";
  return CATEGORIES.find((c) => c.value === value)?.label ?? value;
}

export default function LocationsPage() {
  const { toast } = useToast();
  const [picked, setPicked] = useState<LatLon | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("otro");

  const { data, isLoading } = useQuery<SavedLocation[]>({
    queryKey: ["/api/locations"],
  });
  const locations = data ?? [];

  const createMutation = useMutation({
    mutationFn: async (): Promise<SavedLocation> => {
      const body: LocationCreate = {
        name: name.trim(),
        description: description.trim() || undefined,
        lat: picked![0],
        lon: picked![1],
        category,
      };
      const res = await apiRequest("POST", "/api/locations", body);
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/locations"] });
      toast({ title: "Ubicación guardada", description: `"${name.trim()}" se agregó a tu lista.` });
      setName("");
      setDescription("");
      setCategory("otro");
      setPicked(null);
    },
    onError: () => {
      toast({
        variant: "destructive",
        title: "No se pudo guardar",
        description: "Revisa la conexión con el backend e inténtalo de nuevo.",
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      await apiRequest("DELETE", `/api/locations/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/locations"] });
      toast({ title: "Ubicación eliminada" });
    },
    onError: () => {
      toast({
        variant: "destructive",
        title: "No se pudo eliminar",
        description: "Revisa la conexión con el backend e inténtalo de nuevo.",
      });
    },
  });

  const canSave = name.trim().length > 0 && picked !== null && !createMutation.isPending;

  // Puntos en el mapa: ubicaciones guardadas + el punto seleccionado.
  const dots: DotMarker[] = [
    ...locations.map((loc) => ({
      position: [loc.lat, loc.lon] as LatLon,
      color: CATEGORY_COLOR[loc.category ?? "otro"] ?? CATEGORY_COLOR.otro,
      popup: `${loc.name} · ${categoryLabel(loc.category)}`,
    })),
    ...(picked
      ? [{ position: picked, color: "#0f766e", pulse: true, popup: "Nueva ubicación" } as DotMarker]
      : []),
  ];

  return (
    <AppShell>
      <PageHeader
        icon={<Bookmark size={22} />}
        title="Ubicaciones guardadas"
        subtitle="Guarda lugares frecuentes haciendo clic en el mapa y reutilízalos en tus rutas."
      />

      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        {/* Mapa */}
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Crosshair className="h-4 w-4" />
            <span>Haz clic en el mapa para fijar la latitud y longitud de la nueva ubicación.</span>
          </div>
          <BogotaMap
            dots={dots}
            onMapClick={(latlon) => setPicked(latlon)}
            height="520px"
          />
        </div>

        {/* Formulario */}
        <div className="space-y-6">
          <div className="rounded-lg border border-border bg-card p-5">
            <h2 className="mb-4 flex items-center gap-2 text-base font-semibold">
              <Plus className="h-4 w-4 text-primary" />
              Nueva ubicación
            </h2>

            <div className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="loc-name">Nombre</Label>
                <Input
                  id="loc-name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Ej. Universidad Distrital"
                  data-testid="input-location-name"
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="loc-desc">Descripción (opcional)</Label>
                <Input
                  id="loc-desc"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Ej. Sede Tecnológica"
                  data-testid="input-location-description"
                />
              </div>

              <div className="space-y-1.5">
                <Label>Categoría</Label>
                <Select value={category} onValueChange={setCategory}>
                  <SelectTrigger data-testid="select-location-category">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CATEGORIES.map((c) => (
                      <SelectItem key={c.value} value={c.value}>
                        {c.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="rounded-md bg-muted/60 px-3 py-2 text-sm">
                {picked ? (
                  <span className="tabular text-foreground" data-testid="text-picked-coords">
                    {picked[0].toFixed(5)}, {picked[1].toFixed(5)}
                  </span>
                ) : (
                  <span className="text-muted-foreground">
                    Selecciona un punto en el mapa…
                  </span>
                )}
              </div>

              <Button
                className="w-full"
                disabled={!canSave}
                onClick={() => createMutation.mutate()}
                data-testid="button-save-location"
              >
                {createMutation.isPending ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Plus className="mr-2 h-4 w-4" />
                )}
                Guardar ubicación
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Lista de ubicaciones */}
      <div className="mt-8">
        <h2 className="mb-4 flex items-center gap-2 text-base font-semibold">
          <MapPin className="h-4 w-4 text-primary" />
          Tus ubicaciones
          <span className="text-sm font-normal text-muted-foreground">
            ({locations.length})
          </span>
        </h2>

        {isLoading ? (
          <div className="flex items-center gap-2 text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Cargando ubicaciones…
          </div>
        ) : locations.length === 0 ? (
          <EmptyState
            icon={<Bookmark size={28} />}
            title="Aún no tienes ubicaciones"
            message="Haz clic en el mapa, completa el formulario y guarda tu primer lugar frecuente."
          />
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {locations.map((loc) => (
              <div
                key={loc.id}
                className="group flex items-start justify-between gap-3 rounded-lg border border-border bg-card p-4"
                data-testid={`card-location-${loc.id}`}
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span
                      className="h-2.5 w-2.5 shrink-0 rounded-full"
                      style={{ backgroundColor: CATEGORY_COLOR[loc.category ?? "otro"] ?? CATEGORY_COLOR.otro }}
                    />
                    <h3 className="truncate font-medium" data-testid={`text-location-name-${loc.id}`}>
                      {loc.name}
                    </h3>
                  </div>
                  {loc.description && (
                    <p className="mt-0.5 truncate text-sm text-muted-foreground">
                      {loc.description}
                    </p>
                  )}
                  <div className="mt-2 flex items-center gap-3 text-xs text-muted-foreground">
                    <span className="inline-flex items-center gap-1">
                      <Tag className="h-3 w-3" />
                      {categoryLabel(loc.category)}
                    </span>
                    <span className="tabular">
                      {loc.lat.toFixed(4)}, {loc.lon.toFixed(4)}
                    </span>
                  </div>
                </div>

                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 shrink-0 text-muted-foreground hover:text-destructive"
                      data-testid={`button-delete-location-${loc.id}`}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>¿Eliminar "{loc.name}"?</AlertDialogTitle>
                      <AlertDialogDescription>
                        Esta acción no se puede deshacer. La ubicación se quitará de tu lista.
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>Cancelar</AlertDialogCancel>
                      <AlertDialogAction
                        onClick={() => deleteMutation.mutate(loc.id)}
                        data-testid={`confirm-delete-location-${loc.id}`}
                      >
                        Eliminar
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </div>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
