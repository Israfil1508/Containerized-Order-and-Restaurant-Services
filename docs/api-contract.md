# API contract

## Restaurant Service (`http://localhost:8081`)

### `GET /healthz`
`200`: `{"status":"ok","service":"restaurant"}`

### `GET /restaurants`
Returns restaurant summaries (IDs, names, addresses and availability).

### `GET /restaurants/{restaurant_id}`
Returns restaurant detail including menu. Unknown ID: `404`.

## Order Service (`http://localhost:8080`)

### `GET /healthz`
`200`: `{"status":"ok","service":"order"}`

### `POST /orders`
Request:
```json
{"restaurant_id":"rest-001","items":[{"menu_item_id":"item-001","quantity":2}]}
```
Success (`201`):
```json
{"order_id":"<uuid>","status":"created","created_at":"<UTC ISO-8601>","correlation_id":"<uuid-or-client-value>"}
```
Errors: `422` invalid/missing fields or non-positive/out-of-range quantity; `404` unknown restaurant/menu item; `400` unavailable menu item; `503` Restaurant Service timeout, connection failure or server error.

### `GET /orders/{order_id}`
Returns full order record (`200`); unknown order: `404`.

`X-Correlation-ID` can be supplied to `POST /orders`. If absent, the Order Service generates a UUID. It forwards the ID to Restaurant Service and returns it in the response header and JSON body.
