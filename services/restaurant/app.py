from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="Restaurant Service", version="1.0.0")

# Static seed catalogue: 6 restaurants and 18 menu items.
RESTAURANTS = {
    "rest-001": {"id": "rest-001", "name": "Dhaka Kitchen", "address": "Dhanmondi, Dhaka", "available": True, "menu": [
        {"id": "item-001", "name": "Chicken Biryani", "price": 220.0, "available": True},
        {"id": "item-002", "name": "Beef Tehari", "price": 250.0, "available": True},
        {"id": "item-003", "name": "Borhani", "price": 60.0, "available": False},
    ]},
    "rest-002": {"id": "rest-002", "name": "Pasta House", "address": "Gulshan, Dhaka", "available": True, "menu": [
        {"id": "item-004", "name": "Alfredo Pasta", "price": 380.0, "available": True},
        {"id": "item-005", "name": "Margherita Pizza", "price": 450.0, "available": True},
        {"id": "item-006", "name": "Lemonade", "price": 100.0, "available": True},
    ]},
    "rest-003": {"id": "rest-003", "name": "Green Bowl", "address": "Uttara, Dhaka", "available": True, "menu": [
        {"id": "item-007", "name": "Caesar Salad", "price": 290.0, "available": True},
        {"id": "item-008", "name": "Grilled Sandwich", "price": 210.0, "available": True},
        {"id": "item-009", "name": "Mango Smoothie", "price": 160.0, "available": True},
    ]},
    "rest-004": {"id": "rest-004", "name": "Chittagong Grill", "address": "Agrabad, Chattogram", "available": True, "menu": [
        {"id": "item-010", "name": "Mezban Beef", "price": 320.0, "available": True},
        {"id": "item-011", "name": "Grilled Prawn", "price": 480.0, "available": True},
        {"id": "item-012", "name": "Coconut Water", "price": 80.0, "available": True},
    ]},
    "rest-005": {"id": "rest-005", "name": "Sylhet Spice", "address": "Zindabazar, Sylhet", "available": True, "menu": [
        {"id": "item-013", "name": "Beef Kala Bhuna", "price": 300.0, "available": True},
        {"id": "item-014", "name": "Seven Layer Tea", "price": 120.0, "available": True},
        {"id": "item-015", "name": "Vegetable Khichuri", "price": 180.0, "available": True},
    ]},
    "rest-006": {"id": "rest-006", "name": "Rajshahi Kitchen", "address": "Shaheb Bazar, Rajshahi", "available": True, "menu": [
        {"id": "item-016", "name": "Mango Chicken Curry", "price": 280.0, "available": True},
        {"id": "item-017", "name": "Hilsa Curry", "price": 420.0, "available": True},
        {"id": "item-018", "name": "Mango Lassi", "price": 140.0, "available": True},
    ]},
}

@app.middleware("http")
async def correlation_header(request: Request, call_next):
    response = await call_next(request)
    correlation_id = request.headers.get("X-Correlation-ID")
    if correlation_id:
        response.headers["X-Correlation-ID"] = correlation_id
    return response

@app.get("/healthz")
def healthz():
    return {"status": "ok", "service": "restaurant"}

@app.get("/restaurants")
def list_restaurants():
    return [{k: v for k, v in r.items() if k != "menu"} for r in RESTAURANTS.values()]

@app.get("/restaurants/{restaurant_id}")
def get_restaurant(restaurant_id: str):
    restaurant = RESTAURANTS.get(restaurant_id)
    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant
