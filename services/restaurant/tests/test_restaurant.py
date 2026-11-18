from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_healthz():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_seed_has_three_restaurants_and_six_items():
    restaurants = client.get("/restaurants").json()
    assert len(restaurants) >= 3
    total_items = sum(len(client.get(f"/restaurants/{r['id']}").json()["menu"]) for r in restaurants)
    assert total_items >= 6

def test_get_restaurant_details():
    response = client.get("/restaurants/rest-001")
    assert response.status_code == 200
    assert response.json()["name"] == "Dhaka Kitchen"

def test_unknown_restaurant_is_404():
    assert client.get("/restaurants/not-real").status_code == 404

def test_correlation_id_is_propagated():
    response = client.get("/restaurants", headers={"X-Correlation-ID": "corr-test-123"})
    assert response.headers["X-Correlation-ID"] == "corr-test-123"
