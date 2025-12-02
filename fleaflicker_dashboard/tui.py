"""Textual TUI entry point powered by shared helpers."""

from __future__ import annotations

import argparse
from typing import Optional

from rich.console import Console
from textual.app import App
from textual.containers import Horizontal
from textual.widgets import DataTable, Footer, Header

from .api import FleaflickerAPI
from .models import (
    free_agent_players_from_json,
    recommend_upgrades,
    roster_players_from_json,
)


class FleaflickerDashboardApp(App):
    """A Textual app that shows roster, free agents, and upgrade suggestions."""

    CSS_PATH = None

    def __init__(self, api: FleaflickerAPI, position: Optional[str] = None):
        super().__init__()
        self.api = api
        self.position = position
        self.roster_players = []
        self.free_agent_players = []
        self.console = Console()

    async def on_mount(self) -> None:
        self.roster_table = DataTable(zebra_stripes=True)
        self.free_agent_table = DataTable(zebra_stripes=True)
        self.recommendation_table = DataTable(zebra_stripes=True)

        headers = ["Name", "Pos", "Team", "Proj", "Last3", "Score"]
        self.roster_table.add_columns(*headers)
        self.free_agent_table.add_columns(*headers)
        self.recommendation_table.add_columns("Free Agent", "Replace", "Diff")

        await self.mount(Header(show_clock=False))
        self.container = Horizontal()
        await self.mount(self.container)
        await self.container.mount(self.roster_table)
        await self.container.mount(self.free_agent_table)
        await self.container.mount(self.recommendation_table)
        await self.mount(Footer())

        self.set_interval(10, self.refresh_data)
        await self.refresh_data()

    async def refresh_data(self) -> None:
        try:
            roster_json = self.api.fetch_roster()
            free_agents_json = self.api.fetch_free_agents(self.position)
        except Exception as exc:
            self.console.print(f"Error fetching data: {exc}")
            return

        self.roster_players = roster_players_from_json(roster_json)
        self.free_agent_players = free_agent_players_from_json(free_agents_json)

        self.roster_table.clear()
        self.free_agent_table.clear()
        self.recommendation_table.clear()

        if not self.roster_players:
            self.console.log("No roster data returned; check league/team IDs and sport.")
        if not self.free_agent_players:
            self.console.log("No free agent data returned; check sport/position filters.")

        for player in self.roster_players:
            self.roster_table.add_row(
                player.name,
                player.position,
                player.team,
                f"{player.projection():.1f}",
                f"{player.last_three():.1f}",
                f"{player.score():.1f}",
            )

        for player in self.free_agent_players:
            self.free_agent_table.add_row(
                player.name,
                player.position,
                player.team,
                f"{player.projection():.1f}",
                f"{player.last_three():.1f}",
                f"{player.score():.1f}",
            )

        recommendations = recommend_upgrades(self.roster_players, self.free_agent_players)
        for free_agent, roster_player, diff in recommendations:
            self.recommendation_table.add_row(
                free_agent.name,
                roster_player.name,
                f"{diff:+.2f}",
            )

def build_app(args: argparse.Namespace) -> FleaflickerDashboardApp:
    api = FleaflickerAPI(league_id=args.league, team_id=args.team, sport=args.sport)
    return FleaflickerDashboardApp(api=api, position=args.position)


def cli_main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Fleaflicker live dashboard TUI")
    parser.add_argument("--league", required=True, help="League ID")
    parser.add_argument("--team", required=True, help="Team ID")
    parser.add_argument("--sport", default="NFL", help="Sport (e.g., NFL)")
    parser.add_argument("--position", help="Filter by position for free agents (optional)")
    args = parser.parse_args(argv)

    app = build_app(args)
    app.run()


__all__ = ["FleaflickerDashboardApp", "cli_main"]
