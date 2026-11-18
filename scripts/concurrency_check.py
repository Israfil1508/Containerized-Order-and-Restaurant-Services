"""Submit 20 simultaneous requests to a running Order Service."""
from concurrent.futures import ThreadPoolExecutor
import json
import urllib.error
import urllib.request

URL = "http://localhost:8080/orders"
PAYLOAD = json.dumps({"restaurant_id":"rest-001", "items":[{"menu_item_id":"item-001", "quantity":1}]}).encode()

def submit(_):
    request = urllib.request.Request(URL, data=PAYLOAD, headers={"Content-Type":"application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode()

if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(submit, range(20)))
    ids = [body["order_id"] for status, body in results if status == 201]
    print(f"Requests: {len(results)}; successful: {len(ids)}; unique order IDs: {len(set(ids))}")
    if len(ids) != 20 or len(set(ids)) != 20:
        raise SystemExit("FAIL: expected 20 successful requests with 20 unique IDs")
    print("PASS: 20 concurrent orders created with unique IDs")
