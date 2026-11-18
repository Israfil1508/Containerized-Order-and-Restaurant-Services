# Assignment 01 — Containerized Order and Restaurant Services (Python)

Two independent Python/FastAPI microservices. The Order Service validates restaurant and menu item IDs by making real HTTP requests to the Restaurant Service; it does not import or call Restaurant Service functions.

## Requirements
- Python 3.11+ for local execution; Docker + Docker Compose for container execution.
- Services: Restaurant `:8081`, Order `:8080`.
- In-memory order storage protected by `threading.Lock` (intentionally appropriate for Assignment 01).

## Run with Docker (recommended)
From this directory:

```bash
docker compose up --build -d
docker compose ps
curl http://localhost:8081/healthz
curl http://localhost:8080/healthz
```

Compose configures `RESTAURANT_URL=http://restaurant:8081`; do not use localhost from inside the Order container. Stop with `docker compose down`.

## Run locally
Open two terminals from the project root.

Terminal 1:
```bash
cd services/restaurant
python -m venv .venv
# Windows: .venv\Scripts\activate | Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8081
```

Terminal 2:
```bash
cd services/order
python -m venv .venv
# Windows: .venv\Scripts\activate | Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
# Linux/macOS:
RESTAURANT_URL=http://127.0.0.1:8081 uvicorn app:app --host 0.0.0.0 --port 8080
# PowerShell:
# $env:RESTAURANT_URL='http://127.0.0.1:8081'; uvicorn app:app --host 0.0.0.0 --port 8080
```

## API
See [`docs/api-contract.md`](docs/api-contract.md) for complete examples.

- `GET /healthz` — service health.
- `GET /restaurants` — seeded restaurant catalogue.
- `GET /restaurants/{id}` — restaurant details/menu.
- `POST /orders` — validates all restaurant/menu IDs remotely, then creates an order.
- `GET /orders/{id}` — retrieve an order.

Example order:
```bash
curl -X POST http://localhost:8080/orders -H 'Content-Type: application/json' \
  -d '{"restaurant_id":"rest-001","items":[{"menu_item_id":"item-001","quantity":2}]}'
```

## Tests
Each service has its own test suite. Run from the project root:
```bash
python -m pip install -r services/restaurant/requirements-dev.txt
python -m pip install -r services/order/requirements.txt
(cd services/restaurant && python -m pytest -v)
(cd services/order && python -m pytest -v)
```

The tests cover catalogue reads, successful order creation/retrieval, malformed and invalid input, missing entities, downstream timeout/unavailability, and 20 simultaneous creates with unique IDs.

## Mandatory outage and concurrency experiments
1. Start Compose and create an order; record its returned IDs.
2. Stop only the dependency: `docker compose stop restaurant`.
3. Submit the same order again. Order Service should return HTTP `503` within the configured 2-second HTTP timeout (small scheduling overhead may apply).
4. Restart with `docker compose start restaurant`.
5. For concurrency, run `python scripts/concurrency_check.py` while both services are running. It submits 20 concurrent requests and checks that all order IDs are unique.
6. Copy your actual terminal output into `docs/experiment-results.md`; a fill-in template is provided. The sample log is illustrative, not evidence of your own run.

## Design notes
- Correlation IDs are generated per order and forwarded as `X-Correlation-ID` to Restaurant Service.
- Client may supply `X-Correlation-ID`; otherwise one is generated. Responses include it in a response header and order record.
- Downstream HTTP timeout is configurable with `RESTAURANT_TIMEOUT_SECONDS` (default 2 seconds).
- Order IDs use UUID4. All order store reads/writes use one lock.
- Data is deliberately in-memory; orders reset when the Order container restarts. Persistence is outside A1 scope.
