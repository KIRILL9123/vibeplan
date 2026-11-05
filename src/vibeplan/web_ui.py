"""Web UI — built-in plan viewer using Python's http.server."""
import http.server
import json
import webbrowser
from pathlib import Path
from typing import Dict
from urllib.parse import urlparse

from vibeplan.runner import load_plan
from vibeplan.checkpoint import list_checkpoints
from vibeplan.config import get_plan_path


def _render_html(data: Dict, plan_content: str, checkpoints: list) -> str:
    steps = data.get("steps", [])
    total = data.get("total_tokens")
    task = data.get("original_prompt", "Untitled")
    done = sum(1 for s in steps if s.get("status") == "done")
    pct = round(done / len(steps) * 100) if steps else 0

    rows = ""
    for s in steps:
        status_icon = "✅" if s.get("status") == "done" else "⏳"
        spent = s.get("spent", 0) or 0
        budget = s.get("tokens")
        budget_str = f"{budget:,}" if budget else "∞"
        bar_w = int((spent / budget * 100) if budget else 0)
        rows += f"""
        <tr>
            <td>{s['id']}</td>
            <td>{s['name']}</td>
            <td>{status_icon} {s.get('status', 'pending')}</td>
            <td>{budget_str}</td>
            <td>{spent:,}</td>
            <td><div class="bar"><div class="fill" style="width:{min(bar_w, 100)}%"></div></div></td>
        </tr>"""

    cp_lines = ""
    for c in checkpoints:
        cp_lines += f"<li><code>{c['hash'][:8]}</code> — Step {c['step_id']} ({c['step_name']})</li>"

    budget_line = f"{total:,} tokens" if total else "unlimited"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>vibeplan — {task}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0d1117; color: #c9d1d9; padding: 40px; }}
  .container {{ max-width: 900px; margin: 0 auto; }}
  h1 {{ font-size: 24px; margin-bottom: 8px; color: #58a6ff; }}
  .meta {{ color: #8b949e; font-size: 14px; margin-bottom: 24px; }}
  .summary {{ display: flex; gap: 20px; margin-bottom: 24px; }}
  .card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; flex: 1; }}
  .card h3 {{ font-size: 12px; text-transform: uppercase; color: #8b949e; margin-bottom: 4px; }}
  .card .val {{ font-size: 28px; font-weight: 600; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 24px; }}
  th {{ text-align: left; padding: 8px 12px; font-size: 12px; text-transform: uppercase; color: #8b949e; border-bottom: 1px solid #30363d; }}
  td {{ padding: 10px 12px; border-bottom: 1px solid #21262d; font-size: 14px; }}
  .bar {{ width: 100%; height: 6px; background: #21262d; border-radius: 3px; }}
  .fill {{ height: 6px; background: #58a6ff; border-radius: 3px; transition: width 0.3s; }}
  .plan {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; margin-bottom: 24px; }}
  .plan h2 {{ font-size: 16px; margin-bottom: 12px; color: #58a6ff; }}
  .plan pre {{ white-space: pre-wrap; font-size: 13px; line-height: 1.6; color: #c9d1d9; }}
  .checkpoints {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; }}
  .checkpoints h2 {{ font-size: 16px; margin-bottom: 12px; color: #58a6ff; }}
  .checkpoints li {{ margin: 6px 0; font-size: 13px; }}
  code {{ background: #21262d; padding: 2px 6px; border-radius: 4px; font-size: 12px; }}
  .green {{ color: #3fb950; }}
  .blue {{ color: #58a6ff; }}
</style>
</head>
<body>
<div class="container">
  <h1>vibeplan</h1>
  <p class="meta">{task} · Budget: {budget_line}</p>

  <div class="summary">
    <div class="card">
      <h3>Progress</h3>
      <div class="val">{done}/{len(steps)} <span style="font-size:16px;color:#8b949e">steps</span></div>
      <div class="bar" style="margin-top:8px"><div class="fill" style="width:{pct}%"></div></div>
    </div>
    <div class="card">
      <h3>Completed</h3>
      <div class="val green">{pct}%</div>
    </div>
    <div class="card">
      <h3>Total Budget</h3>
      <div class="val blue">{budget_line}</div>
    </div>
  </div>

  <table>
    <tr><th>#</th><th>Step</th><th>Status</th><th>Budget</th><th>Spent</th><th>Usage</th></tr>
    {rows}
  </table>

  <div class="plan">
    <h2>Execution Plan</h2>
    <pre>{plan_content}</pre>
  </div>

  <div class="checkpoints">
    <h2>Checkpoints</h2>
    {"<ul>" + cp_lines + "</ul>" if cp_lines else "<p style='color:#8b949e'>No checkpoints yet.</p>"}
  </div>
</div>
</body>
</html>"""


def run_web_server(project_dir: Path, port: int = 8080, open_browser: bool = True) -> None:
    plan_path = get_plan_path(project_dir)

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/" or parsed.path == "/index.html":
                data = load_plan(project_dir)
                checkpoints = list_checkpoints(project_dir)
                plan_content = plan_path.read_text(encoding="utf-8") if plan_path.exists() else ""
                html = _render_html(data, plan_content, checkpoints)
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(html.encode("utf-8"))
            elif parsed.path == "/api/status":
                data = load_plan(project_dir)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"))
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, fmt, *args) -> None:
            pass

    server = http.server.HTTPServer(("0.0.0.0", port), Handler)
    url = f"http://localhost:{port}"
    print(f"vibeplan Web UI: {url}")
    print("Press Ctrl+C to stop.")

    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()
