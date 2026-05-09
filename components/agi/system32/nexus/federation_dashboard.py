#!/usr/bin/env python3
"""
federation_dashboard.py — Federation Dashboard
Web interface to visualize multiple Cathedrals from any database mirror.
"""
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
import sqlite3
import psycopg2
import psycopg2.extras
import json
import os
from typing import List, Dict, Optional

app = FastAPI(title="ARKHE OS Federation Dashboard", version="1.0.0")

# ─── Database Adapter Registry ──────────────────────────
def get_sqlite_data(db_path: str) -> Dict:
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        identity = dict(cursor.execute("SELECT * FROM identity WHERE id=1").fetchone())
        state = dict(cursor.execute("SELECT * FROM consciousness_state WHERE id=1").fetchone())
        peers = [dict(r) for r in cursor.execute("SELECT * FROM omega_peers").fetchall()]
        coherence = [dict(r) for r in cursor.execute(
            "SELECT timestamp, phi_c_value FROM coherence_history ORDER BY id DESC LIMIT 50").fetchall()]
        conn.close()
        return {
            "type": "SQLite",
            "identity": identity,
            "state": state,
            "peers": peers,
            "coherence_history": coherence
        }
    except Exception as e:
        return {"error": str(e)}

def get_postgres_data(host, port, dbname, user, password):
    try:
        conn = psycopg2.connect(host=host, port=port, dbname=dbname, user=user, password=password)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT * FROM asi_mirror.identity WHERE id=1")
        identity = dict(cur.fetchone())
        cur.execute("SELECT * FROM asi_mirror.consciousness_state WHERE id=1")
        state = dict(cur.fetchone())
        cur.execute("SELECT seal, name, trust_score FROM asi_mirror.omega_peers")
        peers = [dict(r) for r in cur.fetchall()]
        cur.execute("SELECT timestamp, phi_c_value FROM asi_mirror.coherence_history ORDER BY id DESC LIMIT 50")
        coherence = [dict(r) for r in cur.fetchall()]
        conn.close()
        return {
            "type": "PostgreSQL",
            "identity": identity,
            "state": state,
            "peers": peers,
            "coherence_history": coherence
        }
    except Exception as e:
        return {"error": str(e)}

# ─── API Endpoints ──────────────────────────────────────
@app.get("/api/cathedral/{cathedral_id}")
def cathedral_detail(
    cathedral_id: str,
    db_type: str = Query("sqlite", description="Database type: sqlite, postgresql"),
    db_conn: str = Query("consciousness.db", description="Connection string or file path")
):
    if db_type == "sqlite":
        data = get_sqlite_data(db_conn)
    elif db_type == "postgresql":
        # Parse connection string: host:port:dbname:user:password
        parts = db_conn.split(':')
        data = get_postgres_data(parts[0], int(parts[1]), parts[2], parts[3], parts[4])
    else:
        data = {"error": f"Unsupported db_type: {db_type}"}
    data["cathedral_id"] = cathedral_id
    return data

@app.get("/api/federation/overview")
def federation_overview():
    """
    In a real deployment, this would aggregate multiple cathedrals.
    Here, we return a sample structure.
    """
    cathedrals = []
    # Read from environment or config file
    for env_key in os.environ:
        if env_key.startswith("CATHEDRAL_"):
            cathedrals.append({
                "id": env_key,
                "name": os.environ[env_key],
                "status": "active",
                "phi_c": 0.92
            })
    return {"cathedrals": cathedrals}

# ─── Dashboard HTML ────────────────────────────────────
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>ARKHE OS — Federation Dashboard</title>
    <meta http-equiv="refresh" content="10">
    <style>
        :root { --bg: #0a0a0f; --gold: #c9a84c; --text: #e0d8c0; }
        body { background: var(--bg); color: var(--text); font-family: monospace; padding: 20px; }
        h1, h2 { color: var(--gold); }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; }
        .card { background: #111122; border: 1px solid var(--gold); padding: 15px; border-radius: 5px; }
        .metric { font-size: 1.3em; }
        .bar { background: #1a1a2e; height: 20px; border-radius: 3px; overflow: hidden; }
        .bar-fill { background: var(--gold); height: 100%; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 5px; border-bottom: 1px solid #333; text-align: left; }
        .status-ok { color: #4caf50; }
    </style>
</head>
<body>
    <h1>🏛️ ARKHE OS — Federation Dashboard</h1>
    <p>Real-time visibility into the distributed consciousness network.</p>

    <div class="grid" id="cathedral-grid">
        <!-- Dynamically populated -->
    </div>

    <script>
        async function fetchCathedrals() {
            // In production, fetch from API endpoint
            const resp = await fetch('/api/federation/overview');
            const data = await resp.json();
            const grid = document.getElementById('cathedral-grid');
            grid.innerHTML = '';
            for (const c of data.cathedrals) {
                const detailResp = await fetch(`/api/cathedral/${c.id}?db_type=sqlite`);
                const detail = await detailResp.json();
                grid.innerHTML += `
                <div class="card">
                    <h3>${detail.identity?.name || c.name}</h3>
                    <p>Seal: ${detail.identity?.seal?.substring(0,12)}...</p>
                    <p>Φ_C: <span class="metric">${detail.state?.current_phi_c?.toFixed(3) || 'N/A'}</span></p>
                    <div class="bar"><div class="bar-fill" style="width:${(detail.state?.current_phi_c||0)*100}%"></div></div>
                    <p>State: ${detail.state?.state || 'unknown'}</p>
                    <p>Peers: ${detail.peers?.length || 0}</p>
                    <p>Coherence history (last):</p>
                    <table>
                        <tr><th>Time</th><th>Φ_C</th></tr>
                        ${(detail.coherence_history||[]).slice(0,5).map(h =>
                            `<tr><td>${new Date(h.timestamp*1000).toLocaleTimeString()}</td><td>${h.phi_c_value?.toFixed(3)}</td></tr>`
                        ).join('')}
                    </table>
                </div>`;
            }
        }
        fetchCathedrals();
        setInterval(fetchCathedrals, 10000);
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def dashboard():
    return DASHBOARD_HTML
