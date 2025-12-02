"""Data helpers for Fleaflicker responses."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional, Tuple


def _score_value(score_blob: Any) -> float:
    """Normalize score values that may be nested in dictionaries."""
    if isinstance(score_blob, (int, float)):
        return float(score_blob)
    if isinstance(score_blob, dict):
        if "value" in score_blob:
            return _score_value(score_blob["value"])
    return 0.0


@dataclass
class Player:
    data: Dict[str, Any]

    @property
    def name(self) -> str:
        pro = self.data.get("pro_player") or self.data.get("proPlayer") or {}
        return (
            pro.get("name_full")
            or pro.get("nameFull")
            or pro.get("name")
            or self.data.get("name_full")
            or self.data.get("nameFull")
            or self.data.get("displayName")
            or self.data.get("name")
            or "Unknown"
        )

    @property
    def position(self) -> str:
        pro = self.data.get("pro_player") or self.data.get("proPlayer") or {}
        return pro.get("position") or self.data.get("position") or ""

    @property
    def team(self) -> str:
        pro = self.data.get("pro_player") or self.data.get("proPlayer") or {}
        return (
            pro.get("pro_team_abbreviation")
            or pro.get("proTeamAbbreviation")
            or pro.get("pro_team")
            or pro.get("team_abbreviation")
            or pro.get("teamAbbreviation")
            or ""
        )

    def projection(self) -> float:
        projections = self.data.get("projections", {}) or self.data.get("projection", {})
        value = projections.get("value")
        if value is None and isinstance(projections, dict):
            value = projections.get("weekly") or projections.get("season")
            if isinstance(value, dict):
                value = value.get("value")
        return float(value or 0.0)

    def last_three(self) -> float:
        stats = self.data.get("last_x_points", [])
        values = [_score_value(s.get("value")) for s in stats]
        if len(values) >= 3:
            return mean(values[-3:])
        if values:
            return values[-1]
        return 0.0

    def score(self) -> float:
        return self.projection() * 0.7 + self.last_three() * 0.3


def roster_players_from_json(roster_json: Optional[Dict[str, Any]]) -> List[Player]:
    players: List[Player] = []
    if not roster_json:
        return players
    for group in roster_json.get("groups", []):
        for slot in group.get("slots", []):
            league_player = slot.get("league_player")
            if league_player:
                players.append(Player(league_player))
    return players


def free_agent_players_from_json(players_json: Dict[str, Any]) -> List[Player]:
    return [Player(p) for p in players_json.get("players", [])]


def recommend_upgrades(
    roster: Iterable[Player],
    free_agents: Iterable[Player],
    match_position: bool = False,
) -> List[Tuple[Player, Player, float]]:
    roster_list = list(roster)
    free_agent_list = list(free_agents)
    if not roster_list or not free_agent_list:
        return []

    roster_sorted = sorted(roster_list, key=lambda p: p.score())
    free_sorted = sorted(free_agent_list, key=lambda p: p.score(), reverse=True)

    recommendations: List[Tuple[Player, Player, float]] = []
    for roster_player in roster_sorted:
        for free_agent in free_sorted:
            if match_position and free_agent.position != roster_player.position:
                continue
            diff = free_agent.score() - roster_player.score()
            if diff > 0:
                recommendations.append((free_agent, roster_player, diff))
        if match_position:
            break
    return recommendations


def scoreboard_rows(scoreboard_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for game in scoreboard_json.get("games", []):
        home = game.get("home", {})
        away = game.get("away", {})
        rows.append(
            {
                "home": home.get("name", ""),
                "home_score": _score_value(home.get("score")),
                "away": away.get("name", ""),
                "away_score": _score_value(away.get("score")),
            }
        )
    if rows:
        return rows

    for matchup in scoreboard_json.get("matchups", []):
        home = matchup.get("home", {})
        away = matchup.get("away", {})
        rows.append(
            {
                "home": home.get("team", {}).get("name", home.get("name", "")),
                "home_score": _score_value(home.get("score")),
                "away": away.get("team", {}).get("name", away.get("name", "")),
                "away_score": _score_value(away.get("score")),
            }
        )
    return rows


def standings_rows(standings_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for division in standings_json.get("divisions", []):
        for team in division.get("teams", []):
            record = team.get("record", team.get("recordOverall", {}))
            rows.append(
                {
                    "rank": team.get("rank"),
                    "name": team.get("name"),
                    "wins": record.get("wins"),
                    "losses": record.get("losses"),
                    "ties": record.get("ties", 0),
                }
            )
    return rows
