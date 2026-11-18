import asyncio
from concurrent.futures import ThreadPoolExecutor
import uuid
import httpx
import pytest
from fastapi.testclient import TestClient
import app as order_app
from app import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_orders():
    with order_app.STORE_LOCK:
        order_app.ORDERS.clear()
    yield

class FakeRestaurant:
    def __init__(self, status=200, body=None, exception=None):
        self.status, self.body, self.exception = status, body, exception
    async def __aenter__(self): return self
    async def __aexit__(self, *args): return False
    async def get(self, url, headers=None):
        if self.exception: raise self.exception
        return httpx.Response(self.status, json=self.body or {})

@pytest.fixture
def fake_restaurant(monkeypatch):
    state = {"status": 200, "body": {"id":"rest-001", "available":True, "menu":[
        {"id":"item-001", "name":"Biryani", "price":220, "available":True},
        {"id":"item-002", "name":"Drink", "price":50, "available":False}]}, "exception":None}
    class ClientFactory:
        def __init__(self, *args, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return False
        async def get(self, url, headers=None):
            if state["exception"]: raise state["exception"]
            return httpx.Response(state["status"], json=state["body"])
    monkeypatch.setattr(order_app.httpx, "AsyncClient", ClientFactory)
    return state

def test_healthz():
    assert client.get("/healthz").json()["service"] == "order"

def test_create_and_retrieve_order(fake_restaurant):
    response = client.post("/orders", json={"restaurant_id":"rest-001", "items":[{"menu_item_id":"item-001", "quantity":2}]})
    assert response.status_code == 201
    data = response.json()
    assert data["order_id"] and data["correlation_id"] and data["status"] == "created"
    saved = client.get(f"/orders/{data['order_id']}")
    assert saved.status_code == 200
    assert saved.json()["items"][0]["quantity"] == 2

def test_malformed_and_missing_fields_are_422():
    assert client.post("/orders", content="{").status_code == 422
    assert client.post("/orders", json={"restaurant_id":"rest-001"}).status_code == 422

def test_bad_quantity_is_rejected(fake_restaurant):
    for quantity in [0, -1, 100]:
        response = client.post("/orders", json={"restaurant_id":"rest-001", "items":[{"menu_item_id":"item-001", "quantity":quantity}]})
        assert response.status_code == 422

def test_missing_restaurant_returns_404(fake_restaurant):
    fake_restaurant["status"] = 404
    assert client.post("/orders", json={"restaurant_id":"nope", "items":[{"menu_item_id":"item-001", "quantity":1}]}).status_code == 404

def test_missing_menu_item_returns_404(fake_restaurant):
    response = client.post("/orders", json={"restaurant_id":"rest-001", "items":[{"menu_item_id":"missing", "quantity":1}]})
    assert response.status_code == 404

def test_unavailable_menu_item_returns_400(fake_restaurant):
    response = client.post("/orders", json={"restaurant_id":"rest-001", "items":[{"menu_item_id":"item-002", "quantity":1}]})
    assert response.status_code == 400

def test_downstream_connection_failure_returns_503(fake_restaurant):
    fake_restaurant["exception"] = httpx.ConnectError("offline")
    response = client.post("/orders", json={"restaurant_id":"rest-001", "items":[{"menu_item_id":"item-001", "quantity":1}]})
    assert response.status_code == 503

def test_order_not_found_returns_404():
    assert client.get(f"/orders/{uuid.uuid4()}").status_code == 404

def test_twenty_concurrent_orders_have_unique_ids(fake_restaurant):
    payload = {"restaurant_id":"rest-001", "items":[{"menu_item_id":"item-001", "quantity":1}]}
    def create(_):
        return client.post("/orders", json=payload)
    with ThreadPoolExecutor(max_workers=20) as pool:
        responses = list(pool.map(create, range(20)))
    assert all(r.status_code == 201 for r in responses)
    ids = [r.json()["order_id"] for r in responses]
    assert len(ids) == 20 and len(set(ids)) == 20
    with order_app.STORE_LOCK:
        assert len(order_app.ORDERS) == 20

def test_client_correlation_id_is_returned_and_forwarded(fake_restaurant, monkeypatch):
    seen = {}
    original = order_app.httpx.AsyncClient
    class CapturingClient:
        def __init__(self, *args, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return False
        async def get(self, url, headers=None):
            seen.update(headers or {})
            return httpx.Response(200, json=fake_restaurant["body"])
    monkeypatch.setattr(order_app.httpx, "AsyncClient", CapturingClient)
    response = client.post("/orders", headers={"X-Correlation-ID":"my-trace-1"}, json={"restaurant_id":"rest-001", "items":[{"menu_item_id":"item-001", "quantity":1}]})
    assert response.status_code == 201
    assert response.json()["correlation_id"] == "my-trace-1"
    assert seen["X-Correlation-ID"] == "my-trace-1"
