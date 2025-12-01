"""Shared dashboard helpers for CLI entry points."""

from __future__ import annotations

from typing import Optional

from rich.console import Console

from .api import FleaflickerAPI
from .models import (
    free_agent_players_from_json,
    recommend_upgrades,
    roster_players_from_json,
    scoreboard_rows,
    standings_rows,
)
from .tables import player_table, recommendations_table, scoreboard_table, standings_table


class Dashboard:
    """Reusable operations for printing common dashboard views."""

    def __init__(self, api: FleaflickerAPI, console: Optional[Console] = None):
        self.api = api
        self.console = console or Console()

    def compare(self, position: Optional[str] = None) -> None:
        roster_json = self.api.fetch_roster()
        free_agents_json = self.api.fetch_free_agents(position=position)
        roster_players = roster_players_from_json(roster_json)
        free_agent_players = free_agent_players_from_json(free_agents_json)

        if roster_players:
            self.console.print(player_table("Roster", roster_players))
        else:
            self.console.print("No roster data available.")

        self.console.print(player_table("Free Agents", free_agent_players))

        recommendations = recommend_upgrades(
            roster_players,
            free_agent_players,
            match_position=bool(position),
        )
        if recommendations:
            self.console.print(recommendations_table(recommendations))
        else:
            self.console.print("No upgrades recommended.")

    def show_scoreboard(self, scoring_period: Optional[int] = None) -> None:
        scoreboard = self.api.fetch_scoreboard(scoring_period)
        rows = scoreboard_rows(scoreboard)
        if not rows:
            self.console.print("No scoreboard data available.")
            return
        self.console.print(scoreboard_table(rows))

    def show_standings(self) -> None:
        standings = self.api.fetch_standings()
        rows = standings_rows(standings)
        if not rows:
            self.console.print("No standings data available.")
            return
        self.console.print(standings_table(rows))
