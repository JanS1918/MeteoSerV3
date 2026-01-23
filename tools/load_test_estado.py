import time
from statistics import mean

import httpx

BASE_URL = "http://127.0.0.1:8080/estado"
REQUESTS = 50
TIMEOUT = 5.0


def main() -> None:
    latencies = []
    errors = 0
    with httpx.Client(timeout=TIMEOUT) as client:
        for _ in range(REQUESTS):
            start = time.perf_counter()
            try:
                r = client.get(BASE_URL)
                if r.status_code != 200:
                    errors += 1
                else:
                    r.json()
            except Exception:
                errors += 1
            finally:
                latencies.append((time.perf_counter() - start) * 1000)

    print(f"Requests: {REQUESTS}")
    print(f"Errors: {errors}")
    print(f"Latency ms avg: {mean(latencies):.2f}")
    print(f"Latency ms max: {max(latencies):.2f}")


if __name__ == "__main__":
    main()
