"""Unified CLI entrypoint for Fleaflicker dashboards."""

from __future__ import annotations

import argparse
from typing import Optional

from rich.console import Console

from .api import FleaflickerAPI
from .dashboard import Dashboard
from .models import (
    free_agent_players_from_json,
    roster_players_from_json,
    scoreboard_rows,
    standings_rows,
)
from .tables import player_table, scoreboard_table, standings_table
from .tui import FleaflickerDashboardApp


def _add_league_subcommands(subparsers: argparse._SubParsersAction) -> None:
    league = subparsers.add_parser("league", help="League-level views and utilities")
    league_sub = league.add_subparsers(dest="action", required=True)

    scoreboard = league_sub.add_parser("scoreboard", help="Show the league scoreboard")
    scoreboard.add_argument("--league", required=True)
    scoreboard.add_argument("--sport", default="NFL")
    scoreboard.add_argument("--scoring-period", type=int)

    standings = league_sub.add_parser("standings", help="Show league standings")
    standings.add_argument("--league", required=True)
    standings.add_argument("--sport", default="NFL")

    roster = league_sub.add_parser("roster", help="Show a team roster")
    roster.add_argument("--league", required=True)
    roster.add_argument("--team", required=True)
    roster.add_argument("--sport", default="NFL")

    free_agents = league_sub.add_parser("free-agents", help="List free agents")
    free_agents.add_argument("--league", required=True)
    free_agents.add_argument("--sport", default="NFL")
    free_agents.add_argument("--position", help="Filter free agents by position")

    compare = league_sub.add_parser("compare", help="Compare roster against free agents")
    compare.add_argument("--league", required=True)
    compare.add_argument("--team", required=True)
    compare.add_argument("--sport", default="NFL")
    compare.add_argument("--position", help="Filter free agents by position")


def _add_team_subcommands(subparsers: argparse._SubParsersAction) -> None:
    team = subparsers.add_parser("team", help="Team-focused dashboard views")
    team_sub = team.add_subparsers(dest="action", required=True)

    compare = team_sub.add_parser("compare", help="Compare your roster against free agents")
    compare.add_argument("--league", required=True)
    compare.add_argument("--team", required=True)
    compare.add_argument("--sport", default="NBA")
    compare.add_argument("--position", help="Filter free agents by position")

    scoreboard = team_sub.add_parser("scoreboard", help="Show the league scoreboard")
    scoreboard.add_argument("--league", required=True)
    scoreboard.add_argument("--sport", default="NBA")
    scoreboard.add_argument("--scoring-period", type=int)

    standings = team_sub.add_parser("standings", help="Show league standings")
    standings.add_argument("--league", required=True)
    standings.add_argument("--sport", default="NBA")


def _add_tui_subcommand(subparsers: argparse._SubParsersAction) -> None:
    tui = subparsers.add_parser("tui", help="Launch the live Textual dashboard")
    tui.add_argument("--league", required=True)
    tui.add_argument("--team", required=True)
    tui.add_argument("--sport", default="NFL")
    tui.add_argument("--position", help="Filter free agents by position")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Unified Fleaflicker dashboard application (CLI + TUI)"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    _add_league_subcommands(subparsers)
    _add_team_subcommands(subparsers)
    _add_tui_subcommand(subparsers)
    _add_legacy_shortcuts(subparsers)
    return parser


def _handle_league(args: argparse.Namespace, console: Console) -> None:
    api = FleaflickerAPI(args.league, team_id=getattr(args, "team", None), sport=args.sport)
    dashboard = Dashboard(api, console=console)

    if args.action == "scoreboard":
        dashboard.show_scoreboard(scoring_period=args.scoring_period)
    elif args.action == "standings":
        dashboard.show_standings()
    elif args.action == "roster":
        roster_json = api.fetch_roster()
        players = roster_players_from_json(roster_json)
        console.print(player_table("Roster", players))
    elif args.action == "free-agents":
        free_agents_json = api.fetch_free_agents(args.position)
        players = free_agent_players_from_json(free_agents_json)
        console.print(player_table("Free Agents", players))
    elif args.action == "compare":
        dashboard.compare(position=args.position)
    else:
        console.print("Unknown league action.")


def _handle_team(args: argparse.Namespace, console: Console) -> None:
    api = FleaflickerAPI(args.league, team_id=getattr(args, "team", None), sport=args.sport)
    dashboard = Dashboard(api, console=console)

    if args.action == "compare":
        dashboard.compare(position=args.position)
    elif args.action == "scoreboard":
        dashboard.show_scoreboard(scoring_period=args.scoring_period)
    elif args.action == "standings":
        dashboard.show_standings()
    else:
        console.print("Unknown team action.")


def _handle_tui(args: argparse.Namespace) -> None:
    api = FleaflickerAPI(args.league, team_id=args.team, sport=args.sport)
    app = FleaflickerDashboardApp(api=api, position=args.position)
    app.run()


def _add_legacy_shortcuts(subparsers: argparse._SubParsersAction) -> None:
    """Compatibility aliases that map old entry points to the unified CLI."""
    compare = subparsers.add_parser(
        "compare", help="(legacy) Compare a roster against free agents"
    )
    compare.add_argument("--league", required=True)
    compare.add_argument("--team", required=True)
    compare.add_argument("--sport", default="NBA")
    compare.add_argument("--position")

    scoreboard = subparsers.add_parser(
        "scoreboard", help="(legacy) Show league scoreboard"
    )
    scoreboard.add_argument("--league", required=True)
    scoreboard.add_argument("--sport", default="NBA")
    scoreboard.add_argument("--scoring-period", type=int)

    standings = subparsers.add_parser(
        "standings", help="(legacy) Show league standings"
    )
    standings.add_argument("--league", required=True)
    standings.add_argument("--sport", default="NBA")

    roster = subparsers.add_parser("roster", help="(legacy) Show a team roster")
    roster.add_argument("--league", required=True)
    roster.add_argument("--team", required=True)
    roster.add_argument("--sport", default="NFL")

    free_agents = subparsers.add_parser(
        "free-agents", help="(legacy) Show free agents"
    )
    free_agents.add_argument("--league", required=True)
    free_agents.add_argument("--sport", default="NFL")
    free_agents.add_argument("--position")


def main(argv: Optional[list[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    console = Console()

    if args.command == "league":
        _handle_league(args, console)
    elif args.command == "team":
        _handle_team(args, console)
    elif args.command == "tui":
        _handle_tui(args)
    elif args.command in {"compare", "scoreboard", "standings"}:
        args.action = args.command
        _handle_team(args, console)
    elif args.command in {"roster", "free-agents"}:
        args.action = args.command
        _handle_league(args, console)
    else:
        parser.print_help()


__all__ = ["main", "build_parser"]
