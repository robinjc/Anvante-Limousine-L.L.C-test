import threading
import time
import random
from datetime import datetime
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

lock = threading.Lock()
feeds = {
    "feed_1": {"name": "Camera 1 — Main Gate", "status": "active", "last_frame": None, "error_count": 0, "diagnosis": "OK"},
    "feed_2": {"name": "Camera 2 — Parking Lot", "status": "active", "last_frame": None, "error_count": 0, "diagnosis": "OK"},
    "feed_3": {"name": "Camera 3 — Lobby (Unstable)", "status": "active", "last_frame": None, "error_count": 0, "diagnosis": "OK"},
}

STALE_THRESHOLD = 5


def feed_worker(feed_id, fail_rate=0.0):
    while True:
        time.sleep(random.uniform(0.8, 1.2))

        if random.random() < fail_rate:
            with lock:
                feeds[feed_id]["error_count"] += 1
                feeds[feed_id]["status"] = "error"
                feeds[feed_id]["diagnosis"] = f"Frame capture failed (intermittent error #{feeds[feed_id]['error_count']})"
            time.sleep(random.uniform(2, 5))
            with lock:
                feeds[feed_id]["status"] = "recovering"
                feeds[feed_id]["diagnosis"] = "Attempting reconnect..."
            time.sleep(1.5)
            continue

        if random.random() < fail_rate * 0.5:
            with lock:
                feeds[feed_id]["status"] = "frozen"
                feeds[feed_id]["diagnosis"] = "Feed appears frozen — no new frames received"
            time.sleep(random.uniform(4, 8))
            continue

        with lock:
            feeds[feed_id]["last_frame"] = datetime.now().isoformat()
            feeds[feed_id]["status"] = "active"
            feeds[feed_id]["diagnosis"] = "OK"


def watchdog():
    while True:
        time.sleep(2)
        now = datetime.now()
        with lock:
            for fid, data in feeds.items():
                if data["last_frame"] is None:
                    continue
                last = datetime.fromisoformat(data["last_frame"])
                age = (now - last).total_seconds()
                if age > STALE_THRESHOLD and data["status"] == "active":
                    feeds[fid]["status"] = "stale"
                    feeds[fid]["diagnosis"] = f"No frames for {int(age)}s — possible silent freeze"


threading.Thread(target=feed_worker, args=("feed_1", 0.02), daemon=True).start()
threading.Thread(target=feed_worker, args=("feed_2", 0.05), daemon=True).start()
threading.Thread(target=feed_worker, args=("feed_3", 0.25), daemon=True).start()
threading.Thread(target=watchdog, daemon=True).start()


@app.route("/api/feeds")
def get_feeds():
    with lock:
        return jsonify(feeds)


DASHBOARD = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>FeedWatch — Live Feed Monitor</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; padding: 2rem; }
    h1 { font-size: 1.6rem; font-weight: 700; color: #60a5fa; margin-bottom: 0.3rem; }
    p.sub { color: #94a3b8; font-size: 0.85rem; margin-bottom: 2rem; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.2rem; }
    .card { background: #1e293b; border-radius: 12px; padding: 1.4rem; border: 1px solid #334155; }
    .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
    .card h2 { font-size: 1rem; font-weight: 600; color: #cbd5e1; }
    .badge { padding: 0.25rem 0.75rem; border-radius: 999px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; }
    .active    { background: #166534; color: #4ade80; }
    .error     { background: #7f1d1d; color: #f87171; }
    .frozen    { background: #1e3a5f; color: #93c5fd; }
    .stale     { background: #78350f; color: #fbbf24; }
    .recovering{ background: #3b1f6e; color: #c4b5fd; }
    .row { display: flex; justify-content: space-between; margin-bottom: 0.5rem; font-size: 0.85rem; }
    .label { color: #64748b; }
    .value { color: #e2e8f0; font-weight: 500; }
    .diagnosis { margin-top: 0.8rem; background: #0f172a; border-radius: 8px; padding: 0.6rem 0.8rem; font-size: 0.8rem; color: #94a3b8; border-left: 3px solid #334155; }
    .footer { margin-top: 2rem; color: #475569; font-size: 0.75rem; text-align: center; }
  </style>
</head>
<body>
  <h1>🎥 FeedWatch — Live Feed Monitor</h1>
  <p class="sub">Monitoring 3 simulated camera feeds in real time. Auto-refreshes every 2 seconds.</p>
  <div class="grid" id="grid">Loading...</div>
  <div class="footer">Built by Robin Julius Caesar &nbsp;·&nbsp; FeedWatch Demo</div>

  <script>
    function timeSince(iso) {
      if (!iso) return 'No frames yet';
      const diff = (Date.now() - new Date(iso).getTime()) / 1000;
      if (diff < 2) return 'Just now';
      return diff.toFixed(1) + 's ago';
    }

    async function refresh() {
      const res = await fetch('/api/feeds');
      const data = await res.json();
      const grid = document.getElementById('grid');
      grid.innerHTML = Object.entries(data).map(([id, f]) => `
        <div class="card">
          <div class="card-header">
            <h2>${f.name}</h2>
            <span class="badge ${f.status}">${f.status}</span>
          </div>
          <div class="row"><span class="label">Last Frame</span><span class="value">${timeSince(f.last_frame)}</span></div>
          <div class="row"><span class="label">Errors</span><span class="value">${f.error_count}</span></div>
          <div class="diagnosis">🔍 ${f.diagnosis}</div>
        </div>
      `).join('');
    }

    refresh();
    setInterval(refresh, 2000);
  </script>
</body>
</html>
"""

@app.route("/")
def dashboard():
    return render_template_string(DASHBOARD)


if __name__ == "__main__":
    app.run(debug=False, port=5000)
