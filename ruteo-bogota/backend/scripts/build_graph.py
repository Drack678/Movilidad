"""Descarga y cachea la red vial REAL de Bogotá con OSMnx.

Requiere la pila geoespacial (``requirements.txt``: osmnx, geopandas, etc.).
Descarga la red de calles de Bogotá, la normaliza al formato del proyecto y la
guarda en caché como GraphML (``data/bogota_graph.graphml``). La API la cargará
automáticamente al arrancar.

Uso:
    python -m scripts.build_graph                 # red para automóvil (drive)
    python -m scripts.build_graph --type all      # toda la red
    python -m scripts.build_graph --force         # ignora la caché

Nota: la descarga de toda Bogotá puede tardar varios minutos y consumir cientos
de MB de memoria.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings  # noqa: E402


def main() -> None:
    """Descarga la red real de Bogotá y la guarda en caché."""
    parser = argparse.ArgumentParser(description="Descarga la red vial de Bogotá (OSMnx).")
    parser.add_argument("--type", default="drive", help="drive | bike | walk | all")
    parser.add_argument("--force", action="store_true", help="Ignorar la caché.")
    args = parser.parse_args()

    settings = get_settings()

    try:
        from app.graph.osm_builder import download_city_graph
    except ImportError as exc:
        print(f"ERROR: {exc}")
        print("Instala la pila geoespacial con: pip install -r requirements.txt")
        sys.exit(1)

    print(f"Descargando red vial de {settings.city_name} (tipo={args.type})...")
    graph = download_city_graph(
        settings.city_name,
        settings.graph_cache_path,
        network_type=args.type,
        force=args.force,
    )
    # También guardar una copia JSON como respaldo/portabilidad.
    graph.save_json(settings.fallback_graph_path)
    print(
        f"Listo: {graph.n_nodes} nodos, {graph.n_edges} aristas.\n"
        f"  GraphML -> {settings.graph_cache_path}\n"
        f"  JSON    -> {settings.fallback_graph_path}"
    )


if __name__ == "__main__":
    main()
