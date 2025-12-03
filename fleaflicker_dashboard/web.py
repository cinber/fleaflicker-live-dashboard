"""Flask-powered web dashboard for live league data."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from flask import Flask, jsonify, render_template_string
from rich.console import Console

from .api import FleaflickerAPI
from .models import (
    free_agent_players_from_json,
    recommend_upgrades,
    roster_players_from_json,
    scoreboard_rows,
    standings_rows,
)


def _serialize_player(player: Any) -> Dict[str, Any]:
    return {
        "name": player.name,
        "position": player.position,
        "team": player.team,
        "projection": round(player.projection(), 1),
        "last_three": round(player.last_three(), 1),
        "score": round(player.score(), 1),
    }


def _serialize_recommendations(recommendations: Iterable) -> List[Dict[str, Any]]:
    payload = []
    for free_agent, roster_player, diff in recommendations:
        payload.append(
            {
                "free_agent": _serialize_player(free_agent),
                "replace": _serialize_player(roster_player),
                "diff": round(diff, 2),
            }
        )
    return payload


def _build_payload(api: FleaflickerAPI, position: Optional[str]) -> Dict[str, Any]:
    roster_json = api.fetch_roster()
    free_agents_json = api.fetch_free_agents(position)

    roster_players = roster_players_from_json(roster_json or {})
    free_agent_players = free_agent_players_from_json(free_agents_json or {})

    recommendations = recommend_upgrades(
        roster_players,
        free_agent_players,
        match_position=bool(position),
    )

    payload = {
        "meta": {
            "league": api.league_id,
            "team": api.team_id,
            "sport": api.sport,
            "position": position or "Any",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "roster": [_serialize_player(player) for player in roster_players],
        "free_agents": [_serialize_player(player) for player in free_agent_players],
        "recommendations": _serialize_recommendations(recommendations),
        "scoreboard": scoreboard_rows(api.fetch_scoreboard() or {}),
        "standings": standings_rows(api.fetch_standings() or {}),
    }
    return payload


DASHBOARD_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Fleaflicker Live Dashboard</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0f172a;
      --panel: rgba(15, 23, 42, 0.7);
      --card: #111827;
      --accent: #22d3ee;
      --accent-2: #8b5cf6;
      --text: #e2e8f0;
      --muted: #94a3b8;
      --border: rgba(255, 255, 255, 0.08);
      --shadow: 0 10px 40px rgba(0,0,0,0.35);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Space Grotesk", "Segoe UI", sans-serif;
      background: radial-gradient(circle at 20% 20%, rgba(34, 211, 238, 0.12), transparent 30%),
                  radial-gradient(circle at 80% 0%, rgba(139, 92, 246, 0.18), transparent 35%),
                  linear-gradient(120deg, #020617 0%, #0b1223 40%, #0f172a 100%);
      color: var(--text);
      min-height: 100vh;
    }
    .page {
      max-width: 1200px;
      margin: 0 auto;
      padding: 32px 20px 80px;
    }
    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 18px 20px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(8px);
      position: sticky;
      top: 12px;
      z-index: 10;
    }
    .title {
      font-size: 22px;
      font-weight: 700;
      letter-spacing: -0.02em;
    }
    .meta {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      font-size: 14px;
      color: var(--muted);
    }
    .pill {
      padding: 8px 12px;
      border-radius: 12px;
      border: 1px solid var(--border);
      background: rgba(255, 255, 255, 0.04);
      color: var(--text);
    }
    .actions {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    button {
      background: linear-gradient(135deg, var(--accent), var(--accent-2));
      color: #0b1020;
      border: none;
      padding: 10px 14px;
      border-radius: 10px;
      font-weight: 700;
      cursor: pointer;
      box-shadow: var(--shadow);
      transition: transform 120ms ease, box-shadow 120ms ease;
    }
    button:hover { transform: translateY(-1px); box-shadow: 0 12px 24px rgba(34, 211, 238, 0.35); }
    button:active { transform: translateY(0); }
    main { margin-top: 24px; display: grid; gap: 20px; }
    .card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 16px;
      box-shadow: var(--shadow);
    }
    .card h2 {
      margin: 0 0 12px 0;
      font-size: 18px;
      letter-spacing: -0.01em;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 16px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      color: var(--text);
    }
    th, td {
      padding: 8px 10px;
      font-size: 14px;
      border-bottom: 1px solid var(--border);
    }
    th {
      text-align: left;
      color: var(--muted);
      font-weight: 600;
      letter-spacing: 0.01em;
    }
    tr:hover td { background: rgba(255,255,255,0.03); }
    .muted { color: var(--muted); }
    .status {
      font-size: 13px;
      color: var(--muted);
    }
    .error { color: #fca5a5; font-weight: 600; }
    @media (max-width: 720px) {
      header { flex-direction: column; align-items: flex-start; }
      .actions { width: 100%; justify-content: space-between; }
    }
  </style>
</head>
<body>
  <div class="page">
    <header>
      <div>
        <div class="title">Fleaflicker Live Dashboard</div>
        <div class="meta">
          <span class="pill">League {{ league_id }}</span>
          <span class="pill">Team {{ team_id }}</span>
          <span class="pill">Sport {{ sport }}</span>
          <span class="pill">Free Agent Filter: {{ position }}</span>
        </div>
      </div>
      <div class="actions">
        <div class="status" id="status">Waiting for data…</div>
        <button id="refresh">Refresh now</button>
      </div>
    </header>

    <main>
      <div class="grid">
        <div class="card">
          <h2>Roster</h2>
          <table>
            <thead>
              <tr><th>Name</th><th>Pos</th><th>Team</th><th>Proj</th><th>Last 3</th><th>Score</th></tr>
            </thead>
            <tbody id="roster-body"></tbody>
          </table>
        </div>
        <div class="card">
          <h2>Free Agents</h2>
          <table>
            <thead>
              <tr><th>Name</th><th>Pos</th><th>Team</th><th>Proj</th><th>Last 3</th><th>Score</th></tr>
            </thead>
            <tbody id="free-agents-body"></tbody>
          </table>
        </div>
      </div>

      <div class="card">
        <h2>Upgrade Recommendations</h2>
        <table>
          <thead>
            <tr><th>Free Agent</th><th>Replace</th><th>Diff</th></tr>
          </thead>
          <tbody id="recommendations-body"></tbody>
        </table>
      </div>

      <div class="grid">
        <div class="card">
          <h2>Scoreboard</h2>
          <table>
            <thead>
              <tr><th>Home</th><th>Score</th><th>Away</th><th>Score</th></tr>
            </thead>
            <tbody id="scoreboard-body"></tbody>
          </table>
        </div>
        <div class="card">
          <h2>Standings</h2>
          <table>
            <thead>
              <tr><th>Rank</th><th>Team</th><th>W</th><th>L</th><th>T</th></tr>
            </thead>
            <tbody id="standings-body"></tbody>
          </table>
        </div>
      </div>
    </main>
  </div>

  <script>
    const statusEl = document.getElementById("status");
    const refreshBtn = document.getElementById("refresh");

    function renderRows(targetId, rows, columns, emptyLabel) {
      const tbody = document.getElementById(targetId);
      tbody.innerHTML = "";
      if (!rows || rows.length === 0) {
        tbody.innerHTML = `<tr><td class="muted" colspan="${columns.length}">${emptyLabel}</td></tr>`;
        return;
      }
      rows.forEach(row => {
        const tr = document.createElement("tr");
        columns.forEach(key => {
          const td = document.createElement("td");
          td.textContent = row[key] ?? "";
          tr.appendChild(td);
        });
        tbody.appendChild(tr);
      });
    }

    function renderRecommendations(recs) {
      const tbody = document.getElementById("recommendations-body");
      tbody.innerHTML = "";
      if (!recs || recs.length === 0) {
        tbody.innerHTML = `<tr><td class="muted" colspan="3">No upgrades recommended.</td></tr>`;
        return;
      }
      recs.forEach(rec => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${rec.free_agent?.name || ""}</td>
          <td>${rec.replace?.name || ""}</td>
          <td>${rec.diff > 0 ? "+" + rec.diff.toFixed(2) : rec.diff.toFixed(2)}</td>
        `;
        tbody.appendChild(tr);
      });
    }

    async function loadDashboard() {
      statusEl.textContent = "Refreshing…";
      try {
        const response = await fetch("/api/dashboard");
        const data = await response.json();
        if (data.error) {
          statusEl.innerHTML = `<span class="error">${data.error}</span>`;
          return;
        }
        renderRows("roster-body", data.roster, ["name", "position", "team", "projection", "last_three", "score"], "No roster data.");
        renderRows("free-agents-body", data.free_agents, ["name", "position", "team", "projection", "last_three", "score"], "No free agent data.");
        renderRecommendations(data.recommendations);
        renderRows("scoreboard-body", data.scoreboard, ["home", "home_score", "away", "away_score"], "No games found.");
        renderRows("standings-body", data.standings, ["rank", "name", "wins", "losses", "ties"], "No standings available.");
        const timestamp = data.meta?.generated_at || new Date().toISOString();
        statusEl.textContent = `Updated ${new Date(timestamp).toLocaleTimeString()}`;
      } catch (err) {
        statusEl.innerHTML = `<span class="error">${err}</span>`;
      }
    }

    refreshBtn.addEventListener("click", loadDashboard);
    loadDashboard();
    setInterval(loadDashboard, 10000);
  </script>
</body>
</html>
"""


def create_app(api: FleaflickerAPI, position: Optional[str] = None) -> Flask:
    console = Console()
    app = Flask(__name__)

    @app.get("/")
    def index() -> Any:
        return render_template_string(
            DASHBOARD_HTML,
            league_id=api.league_id,
            team_id=api.team_id,
            sport=api.sport,
            position=position or "Any",
        )

    @app.get("/api/dashboard")
    def dashboard_data() -> Any:
        try:
            payload = _build_payload(api, position)
            return jsonify(payload)
        except Exception as exc:  # pragma: no cover - defensive
            console.print(f"[red]Error building dashboard payload:[/red] {exc}")
            return jsonify({"error": str(exc)}), 500

    return app


def run_web_dashboard(
    api: FleaflickerAPI,
    position: Optional[str],
    host: str = "127.0.0.1",
    port: int = 8000,
) -> None:
    """Start the Flask server for the live dashboard."""
    app = create_app(api, position=position)
    app.run(host=host, port=port, debug=False)


__all__ = ["create_app", "run_web_dashboard"]
