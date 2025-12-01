#!/usr/bin/env python3
"""Fleaflicker Live Dashboard TUI

This script provides a live auto-updating dashboard for your Fleaflicker fantasy team.
It fetches your team roster and available free agents every 10 seconds, calculates
 a simple hybrid score (70% projection, 30% last-3-games average), and recommends
 upgrades when free agents outperform your current roster.

Usage:
    python fleaflicker_tui.py --league <LEAGUE_ID> --team <TEAM_ID> --sport NFL --position QB

Dependencies:
    pip install requests rich textual
"""

import argparse
import asyncio
from statistics import mean
import requests
from rich.console import Console
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import DataTable, Header, Footer, Static

API_BASE = "https://www.fleaflicker.com/api"

def fetch_roster(league_id: str, team_id: str, sport: str):
    """Fetch the roster for the given team."""
    url = f"{API_BASE}/FetchRoster"
    params = {"league_id": league_id, "team_id": team_id, "sport": sport}
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def fetch_free_agents(league_id: str, sport: str, position: str | None = None):
    """Fetch free agents available in the league, optionally filtered by position."""
    url = f"{API_BASE}/FetchPlayerListing"
    params = {
        "league_id": league_id,
        "sport": sport,
        "filter.free_agent_only": "true",
        "sort": "SORT_PROJECTIONS",
    }
    if position:
        params["filter.position.eligibility"] = position
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def extract_roster_players(roster_json: dict) -> list:
    """Extract player entries from a roster JSON response."""
    players = []
    for group in roster_json.get("groups", []):
        for slot in group.get("slots", []):
            lp = slot.get("league_player")
            if lp:
                players.append(lp)
    return players

def get_projection(player: dict) -> float:
    """Return the projection value for a player, if available."""
    return player.get("projections", {}).get("value", 0.0)

def get_last_three_avg(player: dict) -> float:
    """Compute the average points over the last three games, if available."""
    stats = player.get("last_x_points", [])
    # Each entry in last_x_points is a dict with 'value' -> {'value': float}
    values = [s.get("value", {}).get("value", 0.0) for s in stats]
    if len(values) >= 3:
        return mean(values[-3:])
    return values[-1] if values else 0.0

def hybrid_score(player: dict) -> float:
    """Calculate a hybrid score for ranking players."""
    return get_projection(player) * 0.7 + get_last_three_avg(player) * 0.3

def recommend_upgrades(roster: list, free_agents: list) -> list:
    """Return a list of upgrade recommendations based on hybrid score."""
    recommendations = []
    if not roster or not free_agents:
        return recommendations
    # Sort roster by ascending score (worst player first)
    sorted_roster = sorted(roster, key=lambda p: hybrid_score(p))
    # Sort free agents by descending score (best free agent first)
    sorted_fa = sorted(free_agents, key=lambda p: hybrid_score(p), reverse=True)
    worst_player = sorted_roster[0]
    worst_score = hybrid_score(worst_player)
    for fa in sorted_fa:
        if hybrid_score(fa) > worst_score:
            recommendations.append({
                "free_agent": fa,
                "replace": worst_player,
                "difference": round(hybrid_score(fa) - worst_score, 2)
            })
    return recommendations

class FleaflickerDashboard(App):
    """A Textual App to display roster, free agents, and recommendations."""

    CSS_PATH = None  # Use default styling

    def __init__(self, league: str, team: str, sport: str, position: str | None = None):
        super().__init__()
        self.league = league
        self.team = team
        self.sport = sport
        self.position = position
        self.roster_data: list = []
        self.free_agent_data: list = []
        self.console = Console()

    async def on_mount(self) -> None:
        """Initialize tables and start the refresh timer."""
        # Create three tables
        self.roster_table = DataTable(zebra_stripes=True)
        self.free_agent_table = DataTable(zebra_stripes=True)
        self.recommendation_table = DataTable(zebra_stripes=True)

        # Add columns
        headers = ["Name", "Pos", "Team", "Proj", "Last3", "Score"]
        self.roster_table.add_columns(*headers)
        self.free_agent_table.add_columns(*headers)
        self.recommendation_table.add_columns("Free Agent", "Replace", "Diff")

        # Compose layout
        self.mount(Header())
        # Use Horizontal container to layout tables side by side
        self.container = Horizontal()
        await self.mount(self.container)
        await self.container.mount(self.roster_table)
        await self.container.mount(self.free_agent_table)
        await self.container.mount(self.recommendation_table)
        self.mount(Footer())

        # Schedule periodic refresh
        self.set_interval(10, self.refresh_data)
        # Perform initial load
        await self.refresh_data()

    async def refresh_data(self) -> None:
        """Fetch new data and update tables."""
        try:
            roster_json = fetch_roster(self.league, self.team, self.sport)
            fa_json = fetch_free_agents(self.league, self.sport, self.position)
        except Exception as e:
            # Display error in console
            self.console.print(f"Error fetching data: {e}")
            return

        self.roster_data = extract_roster_players(roster_json)
        self.free_agent_data = fa_json.get("players", [])

        # Clear existing table rows
        self.roster_table.clear(rows=True)
        self.free_agent_table.clear(rows=True)
        self.recommendation_table.clear(rows=True)

        # Populate roster table
        for player in self.roster_data:
            pp = player["pro_player"]
            row = [
                pp.get("name_full", "Unknown"),
                pp.get("position", ""),
                pp.get("pro_team_abbreviation", ""),
                f"{get_projection(player):.1f}",
                f"{get_last_three_avg(player):.1f}",
                f"{hybrid_score(player):.1f}",
            ]
            self.roster_table.add_row(*row)

        # Populate free agent table
        for player in self.free_agent_data:
            pp = player["pro_player"]
            row = [
                pp.get("name_full", "Unknown"),
                pp.get("position", ""),
                pp.get("pro_team_abbreviation", ""),
                f"{get_projection(player):.1f}",
                f"{get_last_three_avg(player):.1f}",
                f"{hybrid_score(player):.1f}",
            ]
            self.free_agent_table.add_row(*row)

        # Compute and display recommendations
        recommendations = recommend_upgrades(self.roster_data, self.free_agent_data)
        for rec in recommendations:
            fa_pp = rec["free_agent"]["pro_player"]["name_full"]
            rp_pp = rec["replace"]["pro_player"]["name_full"]
            diff = f"{rec['difference']:+.2f}"
            self.recommendation_table.add_row(fa_pp, rp_pp, diff)

    def compose(self) -> ComposeResult:
        """Compose the UI layout. Not used because we mount manually in on_mount."""
        yield

def main():
    parser = argparse.ArgumentParser(description="Fleaflicker live dashboard TUI")
    parser.add_argument("--league", required=True, help="League ID")
    parser.add_argument("--team", required=True, help="Team ID")
    parser.add_argument("--sport", default="NFL", help="Sport (e.g., NFL)")
    parser.add_argument("--position", help="Filter by position for free agents (optional)")
    args = parser.parse_args()

    app = FleaflickerDashboard(league=args.league, team=args.team, sport=args.sport, position=args.position)
    app.run()

if __name__ == "__main__":
    main()
