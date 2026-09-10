from flask import Flask, render_template_string, jsonify, Response
import time
import io
import sys
from script import print_numbers, get_numbers_list

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Python Script Runner &mdash; Render Deployment</title>
  <style>
    :root {
      --bg-primary: #0b0f19;
      --bg-card: #151d30;
      --accent: #38bdf8;
      --accent-hover: #0284c7;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --terminal-bg: #030712;
      --border: #1e293b;
      --success: #22c55e;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
      background-color: var(--bg-primary);
      color: var(--text);
      margin: 0;
      padding: 40px 20px;
      display: flex;
      flex-direction: column;
      align-items: center;
      min-height: 100vh;
      box-sizing: border-box;
    }
    .container {
      max-width: 800px;
      width: 100%;
    }
    .header {
      text-align: center;
      margin-bottom: 30px;
    }
    .header h1 {
      font-size: 28px;
      color: var(--accent);
      margin: 0 0 10px 0;
    }
    .header p {
      color: var(--text-muted);
      margin: 0;
      font-size: 15px;
    }
    .badge {
      display: inline-block;
      background: rgba(34, 197, 94, 0.15);
      color: var(--success);
      padding: 4px 12px;
      border-radius: 9999px;
      font-size: 13px;
      font-weight: 600;
      margin-top: 10px;
      border: 1px solid rgba(34, 197, 94, 0.3);
    }
    .card {
      background: var(--bg-card);
      border-radius: 14px;
      border: 1px solid var(--border);
      padding: 24px;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
    }
    .controls {
      display: flex;
      gap: 15px;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 20px;
      flex-wrap: wrap;
    }
    .btn {
      background: var(--accent);
      color: #0b0f19;
      font-weight: 700;
      border: none;
      padding: 12px 24px;
      border-radius: 8px;
      font-size: 15px;
      cursor: pointer;
      transition: all 0.2s ease;
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }
    .btn:hover {
      background: #7dd3fc;
      transform: translateY(-1px);
    }
    .stats {
      font-size: 14px;
      color: var(--text-muted);
    }
    .terminal-container {
      background: var(--terminal-bg);
      border: 1px solid #111827;
      border-radius: 10px;
      overflow: hidden;
    }
    .terminal-header {
      background: #111827;
      padding: 10px 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-family: monospace;
      font-size: 13px;
      color: var(--text-muted);
    }
    .dots {
      display: flex;
      gap: 6px;
    }
    .dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
    }
    .dot-red { background: #ef4444; }
    .dot-yellow { background: #eab308; }
    .dot-green { background: #22c55e; }
    .terminal-body {
      padding: 16px;
      height: 380px;
      overflow-y: auto;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 13px;
      line-height: 1.6;
      color: #e2e8f0;
      white-space: pre-wrap;
    }
    .terminal-body::-webkit-scrollbar {
      width: 8px;
    }
    .terminal-body::-webkit-scrollbar-thumb {
      background: #334155;
      border-radius: 4px;
    }
    .footer {
      text-align: center;
      margin-top: 30px;
      font-size: 13px;
      color: var(--text-muted);
    }
    .footer a {
      color: var(--accent);
      text-decoration: none;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Python Script Runner</h1>
      <p>Render-Ready Web Service with Live Execution Output</p>
      <div class="badge">Active & Ready to Deploy</div>
    </div>

    <div class="card">
      <div class="controls">
        <button id="runBtn" class="btn" onclick="runScript()">
          <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
          Run Script (1 to 1000)
        </button>
        <div id="stats" class="stats">Status: Ready to execute</div>
      </div>

      <div class="terminal-container">
        <div class="terminal-header">
          <div class="dots">
            <span class="dot dot-red"></span>
            <span class="dot dot-yellow"></span>
            <span class="dot dot-green"></span>
          </div>
          <span>python script.py (stdout)</span>
          <span id="lineCount">0 lines</span>
        </div>
        <div id="terminal" class="terminal-body">Press "Run Script" to execute Python script and stream numbers 1 to 1000...</div>
      </div>
    </div>

    <div class="footer">
      Ready for instant deployment on <a href="https://render.com" target="_blank">Render.com</a>
    </div>
  </div>

  <script>
    async function runScript() {
      const btn = document.getElementById('runBtn');
      const term = document.getElementById('terminal');
      const stats = document.getElementById('stats');
      const lineCount = document.getElementById('lineCount');

      btn.disabled = true;
      btn.innerText = 'Running...';
      stats.innerText = 'Executing script.py...';
      term.innerText = 'Initializing execution...\\n';

      const startTime = performance.now();

      try {
        const response = await fetch('/api/run');
        const data = await response.json();
        
        term.innerText = data.output;
        term.scrollTop = term.scrollHeight;

        const duration = Math.round(performance.now() - startTime);
        stats.innerText = `Completed in ${duration} ms (Generated ${data.total} numbers)`;
        lineCount.innerText = `${data.total + 2} lines`;
      } catch (err) {
        term.innerText += `\\n[ERROR] Failed to run script: ${err.message}`;
        stats.innerText = 'Execution Failed';
      } finally {
        btn.disabled = false;
        btn.innerHTML = '<svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg> Run Script (1 to 1000)';
      }
    }
  </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/run")
def api_run():
    """Captures stdout of script.py and returns numbers 1 to 1000 in JSON."""
    captured_output = io.StringIO()
    sys.stdout = captured_output
    
    start_time = time.time()
    print_numbers(1, 1000)
    sys.stdout = sys.__stdout__
    
    elapsed = round((time.time() - start_time) * 1000, 2)
    output_text = captured_output.getvalue()
    
    return jsonify({
        "status": "success",
        "total": 1000,
        "elapsed_ms": elapsed,
        "output": output_text
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
