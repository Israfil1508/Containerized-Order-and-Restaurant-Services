import os
import threading
import uuid
from datetime import datetime, timezone
from typing import Dict, List

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict

app = FastAPI(title="Order Service", version="1.0.0")
RESTAURANT_URL = os.getenv("RESTAURANT_URL", "http://127.0.0.1:8081").rstrip("/")
RESTAURANT_TIMEOUT_SECONDS = float(os.getenv("RESTAURANT_TIMEOUT_SECONDS", "2"))

# In-memory A1 store. Every access is guarded by STORE_LOCK.
ORDERS: Dict[str, dict] = {}
STORE_LOCK = threading.Lock()

class OrderItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    menu_item_id: str = Field(min_length=1)
    quantity: int = Field(gt=0, le=99)

class CreateOrder(BaseModel):
    model_config = ConfigDict(extra="forbid")
    restaurant_id: str = Field(min_length=1)
    items: List[OrderItem] = Field(min_length=1)

@app.middleware("http")
async def add_correlation_header(request: Request, call_next):
    response = await call_next(request)
    cid = getattr(request.state, "correlation_id", None)
    if cid:
        response.headers["X-Correlation-ID"] = cid
    return response

async def restaurant_get(path: str, correlation_id: str):
    url = f"{RESTAURANT_URL}{path}"
    try:
        async with httpx.AsyncClient(timeout=RESTAURANT_TIMEOUT_SECONDS) as client:
            response = await client.get(url, headers={"X-Correlation-ID": correlation_id})
    except (httpx.TimeoutException, httpx.ConnectError, httpx.RequestError):
        raise HTTPException(status_code=503, detail="Restaurant Service unavailable")
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Restaurant or menu item not found")
    if response.status_code >= 500:
        raise HTTPException(status_code=503, detail="Restaurant Service unavailable")
    if response.status_code >= 400:
        raise HTTPException(status_code=503, detail="Restaurant Service returned an unexpected error")
    try:
        return response.json()
    except ValueError:
        raise HTTPException(status_code=503, detail="Restaurant Service returned invalid data")

@app.get("/healthz")
def healthz():
    return {"status": "ok", "service": "order"}

@app.post("/orders", status_code=201)
async def create_order(payload: CreateOrder, request: Request, x_correlation_id: str | None = Header(default=None)):
    correlation_id = x_correlation_id or str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    restaurant = await restaurant_get(f"/restaurants/{payload.restaurant_id}", correlation_id)
    if not restaurant.get("available", False):
        raise HTTPException(status_code=404, detail="Restaurant is unavailable")

    menu_by_id = {item.get("id"): item for item in restaurant.get("menu", [])}
    validated_items = []
    for requested in payload.items:
        menu_item = menu_by_id.get(requested.menu_item_id)
        if menu_item is None:
            raise HTTPException(status_code=404, detail=f"Menu item not found: {requested.menu_item_id}")
        if not menu_item.get("available", False):
            raise HTTPException(status_code=400, detail=f"Menu item unavailable: {requested.menu_item_id}")
        validated_items.append({"menu_item_id": requested.menu_item_id, "name": menu_item.get("name"),
                                "quantity": requested.quantity, "unit_price": menu_item.get("price")})

    order_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    order = {"order_id": order_id, "correlation_id": correlation_id, "restaurant_id": payload.restaurant_id,
             "items": validated_items, "status": "created", "created_at": created_at}
    with STORE_LOCK:
        ORDERS[order_id] = order
    return {"order_id": order_id, "status": order["status"], "created_at": created_at,
            "correlation_id": correlation_id}

@app.get("/orders/{order_id}")
def get_order(order_id: str, request: Request):
    with STORE_LOCK:
        order = ORDERS.get(order_id)
        if order is not None:
            order = dict(order)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    request.state.correlation_id = order["correlation_id"]
    return order
