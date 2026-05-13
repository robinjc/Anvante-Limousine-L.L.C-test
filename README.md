# Anvante-Limousine-L.L.C-test
Test
# FeedWatch — Real-Time Feed Monitor

A minimal full-stack demo simulating 3 live camera feeds with independent workers, intermittent failures, and a live dashboard showing feed status, last frame time, error count, and diagnosis.

---

## Setup & Run

### Requirements
- Python 3.8+
- Flask (`pip install flask`)

### Run
```bash
python app.py
```

Then open: **http://localhost:5000**

---

## What It Does

- Simulates **3 independent camera feeds** using Python threads
- Each feed emits frame events every ~1 second
- **Feed 3 (Lobby)** is intentionally unreliable — randomly freezes or throws errors
- A **watchdog thread** detects silent freezes (feeds that stop emitting without an error)
- A **live dashboard** auto-refreshes every 2 seconds showing:
  - Feed status (active / error / frozen / stale / recovering)
  - Last frame time
  - Error count
  - Short diagnosis for each feed
- REST API at `/api/feeds` returns JSON feed state

---

## Edge Case Intentionally Handled

**Silent freeze detection via watchdog:**  
A feed can stop emitting frames without throwing any error — it just goes quiet. The worker wouldn't detect this. A separate watchdog thread polls every 2 seconds and marks any feed whose last frame is older than 5 seconds as `stale`, even if no error was reported. This mirrors a real scenario where a camera cable disconnects or a network packet is dropped silently.

---

## AI Tools Used

- **Claude** — used to reason through thread safety tradeoffs (shared state vs isolated workers). Suggested using a single lock for shared feed dict. I accepted this — simple and sufficient for this scope.
- **ChatGPT** — asked it to explain Python threading vs asyncio for this use case. Helped confirm threading was the right choice for I/O-bound simulated feeds.
- **Copilot** — used for boilerplate HTML/CSS in the dashboard. Reviewed and trimmed output significantly — it over-engineered the CSS.

### What I rejected
- Claude suggested using a database (SQLite) for storing frame history. Rejected — overkill for a 30-45 min task. In-memory dict is sufficient.
- Copilot suggested WebSockets for real-time push. Rejected — polling every 2 seconds is simpler, meets the brief, and avoids added complexity.

---

## Tradeoff Made Under Time Limit

Used **polling (every 2s)** instead of WebSockets for the dashboard. WebSockets would give true real-time updates but add significant setup complexity. For a monitoring dashboard where 2-second lag is acceptable, polling is the right pragmatic choice. If this were production, WebSockets or SSE would be the upgrade path.

---

## Stack
- **Backend:** Python + Flask
- **Frontend:** Vanilla HTML/CSS/JS (single file, no build step)
- **Concurrency:** Python threading with a shared lock
- **API:** REST (`/api/feeds`)

---

Built by **Robin Julius Caesar** — Dubai, UAE  
robinjuliuscaesar@gmail.com | github.com/robinjc
