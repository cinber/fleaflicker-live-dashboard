"""HTTP client for the Fleaflicker API."""

from __future__ import annotations

from typing import Any, Dict, Optional

import requests
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

API_BASE = "https://www.fleaflicker.com/api"
DEFAULT_TIMEOUT = 15


class ApiError(RuntimeError):
    """Raised when the Fleaflicker API call fails."""


def _build_session() -> Session:
    session = requests.Session()
    retry = Retry(
        total=3,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        backoff_factor=0.5,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


class FleaflickerAPI:
    """Lightweight wrapper around Fleaflicker endpoints."""

    def __init__(self, league_id: str, team_id: Optional[str] = None, sport: str = "NFL"):
        self.league_id = league_id
        self.team_id = team_id
        self.sport = sport
        self.session = _build_session()

    def _get(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{API_BASE}/{path}"
        try:
            response = self.session.get(url, params=params, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            raise ApiError(f"Request to {path} failed: {exc}") from exc
        except ValueError as exc:
            raise ApiError(f"Invalid JSON response from {path}") from exc

    def fetch_roster(self, team_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Return a roster payload for the requested team, or None if no team id."""
        target_team = team_id or self.team_id
        if not target_team:
            return None
        params = {"league_id": self.league_id, "team_id": target_team, "sport": self.sport}
        return self._get("FetchRoster", params)

    def fetch_free_agents(self, position: Optional[str] = None) -> Dict[str, Any]:
        """Return a player listing payload for free agents."""
        params = {
            "league_id": self.league_id,
            "sport": self.sport,
            "filter.free_agent_only": "true",
            "sort": "SORT_PROJECTIONS",
        }
        if position:
            params["filter.position.eligibility"] = position
        return self._get("FetchPlayerListing", params)

    def fetch_scoreboard(self, scoring_period: Optional[int] = None) -> Dict[str, Any]:
        """Return a league scoreboard payload."""
        params = {"league_id": self.league_id, "sport": self.sport}
        if scoring_period is not None:
            params["scoring_period"] = scoring_period
        return self._get("FetchLeagueScoreboard", params)

    def fetch_standings(self) -> Dict[str, Any]:
        """Return a league standings payload."""
        params = {"league_id": self.league_id, "sport": self.sport}
        return self._get("FetchLeagueStandings", params)
