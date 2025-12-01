"""Rich table builders used across dashboards."""

from __future__ import annotations

from typing import Iterable, List, Tuple

from rich.table import Table

from .models import Player


def player_table(title: str, players: Iterable[Player]) -> Table:
    table = Table(title=title)
    table.add_column("Name")
    table.add_column("Pos")
    table.add_column("Team")
    table.add_column("Proj", justify="right")
    table.add_column("Last3", justify="right")
    table.add_column("Score", justify="right")
    for player in players:
        table.add_row(
            player.name,
            player.position,
            player.team,
            f"{player.projection():.1f}",
            f"{player.last_three():.1f}",
            f"{player.score():.1f}",
        )
    return table


def recommendations_table(recommendations: Iterable[Tuple[Player, Player, float]]) -> Table:
    table = Table(title="Upgrade Recommendations")
    table.add_column("Free Agent")
    table.add_column("Replace")
    table.add_column("Diff", justify="right")
    for free_agent, roster_player, diff in recommendations:
        table.add_row(free_agent.name, roster_player.name, f"+{diff:.1f}")
    return table


def scoreboard_table(matchups: List[dict]) -> Table:
    table = Table(title="League Scoreboard")
    table.add_column("Home Team")
    table.add_column("Home Score", justify="right")
    table.add_column("Away Team")
    table.add_column("Away Score", justify="right")
    for game in matchups:
        table.add_row(
            game.get("home", ""),
            f"{game.get('home_score', '')}",
            game.get("away", ""),
            f"{game.get('away_score', '')}",
        )
    return table


def standings_table(standings: List[dict]) -> Table:
    table = Table(title="League Standings")
    table.add_column("Rank", justify="right")
    table.add_column("Team")
    table.add_column("Wins", justify="right")
    table.add_column("Losses", justify="right")
    table.add_column("Ties", justify="right")
    for entry in standings:
        table.add_row(
            str(entry.get("rank", "")),
            entry.get("name", ""),
            str(entry.get("wins", "")),
            str(entry.get("losses", "")),
            str(entry.get("ties", "")),
        )
    return table
