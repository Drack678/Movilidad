"""Tests de integración de la API REST.

Usan ``TestClient`` de FastAPI. Se fuerza el uso del grafo representativo
(``USE_REAL_GRAPH=0``) para no depender de OSMnx ni de la red durante los tests.
"""

from __future__ import annotations

import os

os.environ["USE_REAL_GRAPH"] = "0"

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Cliente de pruebas con el ciclo de vida (startup) ejecutado."""
    with TestClient(app) as c:
        yield c


def test_health(client: TestClient) -> None:
    """El endpoint de salud debe responder 'ok'."""
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ready_reports_graph(client: TestClient) -> None:
    """El endpoint /ready debe reportar nodos y aristas del grafo cargado."""
    r = client.get("/api/ready")
    assert r.status_code == 200
    body = r.json()
    assert body["ready"] is True
    assert body["n_nodes"] > 0
    assert body["n_edges"] > 0


def test_locations_crud(client: TestClient) -> None:
    """Crear, listar y eliminar una ubicación debe funcionar de extremo a extremo."""
    payload = {
        "name": "Universidad Distrital",
        "description": "Sede Tecnológica",
        "lat": 4.5765,
        "lon": -74.1188,
        "category": "universidad",
    }
    created = client.post("/api/locations", json=payload)
    assert created.status_code == 201
    loc_id = created.json()["id"]

    listed = client.get("/api/locations")
    assert listed.status_code == 200
    assert any(loc["id"] == loc_id for loc in listed.json())

    deleted = client.delete(f"/api/locations/{loc_id}")
    assert deleted.status_code == 204


def test_calculate_route(client: TestClient) -> None:
    """El cálculo de ruta debe devolver una ruta con coordenadas."""
    payload = {
        "origin_lat": 4.52,
        "origin_lon": -74.17,
        "dest_lat": 4.76,
        "dest_lon": -74.04,
        "mode": "car",
        "algorithm": "dijkstra",
    }
    r = client.post("/api/route", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["found"] is True
    assert len(body["coordinates"]) >= 2
    assert body["total_distance_m"] > 0


def test_compare_algorithms(client: TestClient) -> None:
    """La comparación debe devolver métricas para ACO, Dijkstra y A*."""
    payload = {
        "origin_lat": 4.52,
        "origin_lon": -74.17,
        "dest_lat": 4.70,
        "dest_lon": -74.06,
        "mode": "car",
        "algorithm": "aco",
        "aco_params": {"n_ants": 8, "n_iterations": 10, "seed": 1},
    }
    r = client.post("/api/route/compare", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert len(body["results"]) == 3
    assert body["best_algorithm"] in {"aco", "dijkstra", "astar"}


def test_traffic_generate_and_heatmap(client: TestClient) -> None:
    """Generar tráfico y pedir el heatmap debe devolver datos con color."""
    gen = client.post("/api/traffic/generate", json={"strategy": "rush_hour"})
    assert gen.status_code == 200
    assert "distribution" in gen.json()

    hm = client.get("/api/traffic/heatmap?limit=50")
    assert hm.status_code == 200
    data = hm.json()
    assert len(data) <= 50
    assert all("color" in e for e in data)


def test_analytics_stats(client: TestClient) -> None:
    """El dashboard de analítica debe reportar nodos, aristas y congestión."""
    r = client.get("/api/analytics/stats")
    assert r.status_code == 200
    body = r.json()
    assert body["n_nodes"] > 0
    assert body["n_edges"] > 0
    assert isinstance(body["most_congested"], list)
