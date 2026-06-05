"""Construcción del grafo vial REAL desde OpenStreetMap usando OSMnx.

Este módulo es el único que importa OSMnx/GeoPandas. Se mantiene aislado para
que el resto del backend funcione sin esas dependencias pesadas (usando el
grafo representativo en ``data/bogota_graph.json``).

Flujo:
1. ``download_city_graph`` descarga la red vial de la ciudad con OSMnx,
   completa velocidades/tiempos y la guarda en caché (GraphML).
2. ``osmnx_to_road_graph`` convierte el ``MultiDiGraph`` de OSMnx en el
   :class:`RoadGraph` propio del proyecto (DiGraph simple con atributos
   normalizados).
"""

from __future__ import annotations

from pathlib import Path

import networkx as nx

from app.graph.road_graph import RoadGraph, _DEFAULT_SPEED_KPH, _HIGHWAY_SPEED_KPH


def _first(value: object, default: object) -> object:
    """OSM a veces devuelve listas en atributos; toma el primer valor."""
    if isinstance(value, list):
        return value[0] if value else default
    return value if value is not None else default


def _parse_speed_kph(maxspeed: object, highway: str) -> float:
    """Interpreta el atributo ``maxspeed`` de OSM; si falta usa el tipo de vía."""
    raw = _first(maxspeed, None)
    if raw is not None:
        try:
            # 'maxspeed' puede venir como '50' o '50 km/h'.
            return float(str(raw).split()[0])
        except (ValueError, IndexError):
            pass
    return _HIGHWAY_SPEED_KPH.get(highway, _DEFAULT_SPEED_KPH)


def osmnx_to_road_graph(mg: "nx.MultiDiGraph") -> RoadGraph:
    """Convierte un ``MultiDiGraph`` de OSMnx en un :class:`RoadGraph`.

    Se colapsan las aristas paralelas quedándose con la más corta y se
    normalizan los atributos (longitud, tipo de vía, velocidad, tiempo base).
    """
    g = nx.DiGraph()

    # Nodos: OSMnx guarda lon en 'x' y lat en 'y'.
    for nid, data in mg.nodes(data=True):
        g.add_node(int(nid), x=float(data["x"]), y=float(data["y"]))

    # Aristas: colapsar paralelas, normalizar atributos.
    for u, v, data in mg.edges(data=True):
        u, v = int(u), int(v)
        length = float(_first(data.get("length"), 0.0) or 0.0)
        if length <= 0:
            continue
        highway = str(_first(data.get("highway"), "unclassified"))
        speed = _parse_speed_kph(data.get("maxspeed"), highway)
        base_time = length / (speed * 1000.0 / 3600.0)
        name = str(_first(data.get("name"), ""))

        # Si ya existe la arista, conservar la de menor longitud.
        if g.has_edge(u, v) and g.edges[u, v]["length"] <= length:
            continue
        g.add_edge(
            u,
            v,
            length=length,
            highway=highway,
            speed_kph=speed,
            base_time_s=base_time,
            traffic=0,
            name=name,
        )

    # Obtener la componente fuertemente conexa más grande para evitar nodos aislados
    if g.number_of_nodes() > 0:
        largest_component = max(nx.strongly_connected_components(g), key=len)
        g = g.subgraph(largest_component).copy()

    return RoadGraph(g)


def download_city_graph(
    city_name: str,
    cache_path: Path,
    network_type: str = "drive",
    force: bool = False,
) -> RoadGraph:
    """Descarga (o carga de caché) la red vial real de una ciudad.

    Args:
        city_name: Lugar para OSMnx, p.ej. ``"Bogotá, Colombia"``.
        cache_path: Ruta del archivo GraphML para cachear el grafo de OSMnx.
        network_type: Tipo de red OSM (``drive``, ``bike``, ``walk``, ``all``).
        force: Si ``True``, ignora la caché y vuelve a descargar.

    Returns:
        :class:`RoadGraph` con la red vial normalizada.

    Raises:
        ImportError: Si OSMnx no está instalado.
    """
    try:
        import osmnx as ox
    except ImportError as exc:  # pragma: no cover - depende del entorno
        raise ImportError(
            "OSMnx no está instalado. Instala 'requirements.txt' para descargar "
            "la red vial real, o usa el grafo representativo (data/bogota_graph.json)."
        ) from exc

    cache_path = Path(cache_path)

    if cache_path.exists() and not force:
        mg = ox.load_graphml(cache_path)
    else:
        # Descarga la red vial completa de la ciudad y añade velocidades/tiempos.
        mg = ox.graph_from_place(city_name, network_type=network_type, simplify=True)
        mg = ox.add_edge_speeds(mg)
        mg = ox.add_edge_travel_times(mg)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        ox.save_graphml(mg, cache_path)

    return osmnx_to_road_graph(mg)
