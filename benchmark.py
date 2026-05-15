import argparse
import json
import random
import statistics
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed


PROFILES = {
    "read-heavy": (0.8, 0.2),
    "balanced": (0.5, 0.5),
    "write-heavy": (0.2, 0.8),
}

STRATEGIES = {
    "lazy": "Lazy Loading / Cache-Aside",
    "through": "Write-Through",
    "back": "Write-Back",
}


def request_json(method, url, payload=None):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(request, timeout=10) as response:
        body = response.read().decode("utf-8")
        return json.loads(body) if body else {}


def one_request(base_url, strategy, read_probability):
    item_id = random.randint(1, 1000)
    started = time.perf_counter()
    if random.random() < read_probability:
        request_json("GET", f"{base_url}/{strategy}/{item_id}")
        operation = "read"
    else:
        payload = f"data_{random.randint(1000, 9999)}"
        request_json("POST", f"{base_url}/{strategy}", {"id": item_id, "payload": payload})
        operation = "write"
    return operation, (time.perf_counter() - started) * 1000


def run_case(base_url, strategy, profile, requests, workers):
    read_probability, _ = PROFILES[profile]
    request_json("POST", f"{base_url}/admin/reset")

    latencies = []
    operations = {"read": 0, "write": 0}
    started = time.perf_counter()

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(one_request, base_url, strategy, read_probability)
            for _ in range(requests)
        ]
        for future in as_completed(futures):
            operation, latency = future.result()
            operations[operation] += 1
            latencies.append(latency)

    duration = time.perf_counter() - started
    metrics = request_json("GET", f"{base_url}/metrics")
    return {
        "profile": profile,
        "strategy": strategy,
        "strategy_name": STRATEGIES[strategy],
        "requests": requests,
        "reads": operations["read"],
        "writes": operations["write"],
        "duration_sec": round(duration, 3),
        "throughput_rps": round(requests / duration, 2),
        "avg_latency_ms": round(statistics.mean(latencies), 2),
        "p95_latency_ms": round(statistics.quantiles(latencies, n=20)[18], 2),
        **metrics,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--requests", type=int, default=3000)
    parser.add_argument("--workers", type=int, default=32)
    parser.add_argument("--output", default="benchmark-results.json")
    args = parser.parse_args()

    results = []
    for profile in PROFILES:
        for strategy in STRATEGIES:
            result = run_case(args.base_url, strategy, profile, args.requests, args.workers)
            results.append(result)
            print(
                f"{profile:11} {strategy:7} "
                f"{result['throughput_rps']:8.2f} rps "
                f"{result['avg_latency_ms']:7.2f} ms "
                f"db={result['db_queries']:5} "
                f"hit={result['hit_rate_percent']:6.2f}% "
                f"queue={result['write_back_queue_length']:4}"
            )

    with open(args.output, "w", encoding="utf-8") as file:
        json.dump(results, file, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    try:
        main()
    except urllib.error.URLError as exc:
        raise SystemExit(f"Application is not available: {exc}") from exc
