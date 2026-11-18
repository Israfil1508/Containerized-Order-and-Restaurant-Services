# Mandatory experiment record — fill with your own results

> Do not submit this template as if the experiment was already run. Paste your actual terminal output and timestamps below.

## Environment
- Date/time:
- OS:
- Docker version:
- Compose version:

## 1. Normal operation
Command and response from `GET /healthz` for both services:

```text
PASTE YOUR OUTPUT HERE
```

## 2. Restaurant Service outage
1. Run `docker compose stop restaurant`.
2. POST a valid order to Order Service.
3. Record status code, response body and elapsed time.

```text
PASTE YOUR OUTPUT HERE
```

Expected: HTTP 503 within configured downstream timeout (default 2 seconds plus request overhead).

## 3. Recovery
Run `docker compose start restaurant`, verify health and create an order:

```text
PASTE YOUR OUTPUT HERE
```

## 4. Concurrency
Run `python scripts/concurrency_check.py` and paste output:

```text
PASTE YOUR OUTPUT HERE
```
