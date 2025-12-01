"""HTTP client for the Fleaflicker API."""

from __future__ import annotations

from typing import Any, Dict, Optional

import requests

API_BASE = "https://www.fleaflicker.com/api"


class FleaflickerAPI:
    """Lightweight wrapper around Fleaflicker endpoints."""

    def __init__(self, league_id: str, team_id: Optional[str] = None, sport: str = "NFL"):
        self.league_id = league_id
        self.team_id = team_id
        self.sport = sport

    def fetch_roster(self, team_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Return a roster payload for the requested team, or None if no team id."""
        target_team = team_id or self.team_id
        if not target_team:
            return None
        url = f"{API_BASE}/FetchRoster"
        params = {"league_id": self.league_id, "team_id": target_team, "sport": self.sport}
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def fetch_free_agents(self, position: Optional[str] = None) -> Dict[str, Any]:
        """Return a player listing payload for free agents."""
        url = f"{API_BASE}/FetchPlayerListing"
        params = {
            "league_id": self.league_id,
            "sport": self.sport,
            "filter.free_agent_only": "true",
            "sort": "SORT_PROJECTIONS",
        }
        if position:
            params["filter.position.eligibility"] = position
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def fetch_scoreboard(self, scoring_period: Optional[int] = None) -> Dict[str, Any]:
        """Return a league scoreboard payload."""
        url = f"{API_BASE}/FetchLeagueScoreboard"
        params = {"league_id": self.league_id, "sport": self.sport}
        if scoring_period is not None:
            params["scoring_period"] = scoring_period
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def fetch_standings(self) -> Dict[str, Any]:
        """Return a league standings payload."""
        url = f"{API_BASE}/FetchLeagueStandings"
        params = {"league_id": self.league_id, "sport": self.sport}
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
