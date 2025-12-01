#!/usr/bin/env python3
import requests
from rich.console import Console
from rich.table import Table
from statistics import mean
import argparse

class FleaflickerAPI:
    def __init__(self, league_id, team_id=None, sport="NBA"):
        self.league_id = league_id
        self.team_id = team_id
        self.sport = sport
        self.base = "https://www.fleaflicker.com/api"

    def fetch_roster(self):
        if not self.team_id:
            return None
        url = f"{self.base}/FetchRoster"
        params = {"league_id": self.league_id, "team_id": self.team_id, "sport": self.sport}
        r = requests.get(url, params=params)
        r.raise_for_status()
        return r.json()

    def fetch_free_agents(self, position=None):
        url = f"{self.base}/FetchPlayerListing"
        params = {"league_id": self.league_id, "sport": self.sport,
                  "filter.free_agent_only": "true", "sort": "SORT_PROJECTIONS"}
        if position:
            params["filter.position.eligibility"] = position
        r = requests.get(url, params=params)
        r.raise_for_status()
        return r.json()

    def fetch_scoreboard(self, scoring_period=None):
        url = f"{self.base}/FetchLeagueScoreboard"
        params = {"league_id": self.league_id, "sport": self.sport}
        if scoring_period is not None:
            params["scoring_period"] = scoring_period
        r = requests.get(url, params=params)
        r.raise_for_status()
        return r.json()

    def fetch_standings(self):
        url = f"{self.base}/FetchLeagueStandings"
        params = {"league_id": self.league_id, "sport": self.sport}
        r = requests.get(url, params=params)
        r.raise_for_status()
        return r.json()

class Player:
    def __init__(self, data):
        self.data = data

    @property
    def name(self):
        return self.data["pro_player"]["name_full"]

    @property
    def position(self):
        return self.data["pro_player"]["position"]

    @property
    def team(self):
        return self.data["pro_player"].get("pro_team_abbreviation", "")

    def projection(self):
        return self.data.get("projections", {}).get("value", 0.0)

    def last3(self):
        stats = self.data.get("last_x_points", [])
        values = [s["value"]["value"] for s in stats]
        if len(values) >= 3:
            return mean(values[-3:])
        elif values:
            return values[-1]
        return 0.0

    def score(self):
        return self.projection() * 0.7 + self.last3() * 0.3

class Dashboard:
    def __init__(self, api: FleaflickerAPI):
        self.api = api
        self.console = Console()

    def _extract_roster_players(self, roster_json):
        players = []
        if not roster_json:
            return players
        for group in roster_json.get("groups", []):
            for slot in group.get("slots", []):
                lp = slot.get("league_player")
                if lp:
                    players.append(Player(lp))
        return players

    def _extract_free_agents(self, fa_json):
        return [Player(p) for p in fa_json.get("players", [])]

    def show_table(self, title, players):
        table = Table(title=title)
        table.add_column("Name")
        table.add_column("Pos")
        table.add_column("Team")
        table.add_column("Proj", justify="right")
        table.add_column("Last3", justify="right")
        table.add_column("Score", justify="right")
        for p in players:
            table.add_row(p.name, p.position, p.team, f"{p.projection():.1f}", f"{p.last3():.1f}", f"{p.score():.1f}")
        self.console.print(table)

    def compare(self, position=None):
        roster_json = self.api.fetch_roster()
        fa_json = self.api.fetch_free_agents(position=position)
        roster_players = self._extract_roster_players(roster_json)
        fa_players = self._extract_free_agents(fa_json)

        self.show_table("Roster", roster_players)
        self.show_table("Free Agents", fa_players)

        if not roster_players:
            self.console.print("No roster data available.")
            return

        roster_sorted = sorted(roster_players, key=lambda p: p.score())
        fa_sorted = sorted(fa_players, key=lambda p: p.score(), reverse=True)
        worst = roster_sorted[0]
        recommendations = []
        for fa in fa_sorted:
            if fa.position == worst.position and fa.score() > worst.score():
                recommendations.append((fa, worst))

        if recommendations:
            rec_table = Table(title="Upgrade Recommendations")
            rec_table.add_column("Free Agent")
            rec_table.add_column("Replace")
            rec_table.add_column("Diff", justify="right")
            for fa, old in recommendations:
                diff = fa.score() - old.score()
                rec_table.add_row(fa.name, old.name, f"+{diff:.1f}")
            self.console.print(rec_table)
        else:
            self.console.print("No upgrades recommended.")

    def show_scoreboard(self, scoring_period=None):
        scoreboard = self.api.fetch_scoreboard(scoring_period)
        table = Table(title="League Scoreboard")
        table.add_column("Team 1")
        table.add_column("Score 1", justify="right")
        table.add_column("Team 2")
        table.add_column("Score 2", justify="right")
        for game in scoreboard.get("games", []):
            team1 = game["home"]["name"]
            score1 = game["home"]["score"]
            team2 = game["away"]["name"]
            score2 = game["away"]["score"]
            table.add_row(team1, str(score1), team2, str(score2))
        self.console.print(table)

    def show_standings(self):
        standings = self.api.fetch_standings()
        table = Table(title="League Standings")
        table.add_column("Rank", justify="right")
        table.add_column("Team")
        table.add_column("Wins", justify="right")
        table.add_column("Losses", justify="right")
        for division in standings.get("divisions", []):
            for team in division.get("teams", []):
                rank = team.get("rank")
                name = team.get("name")
                wins = team.get("record", {}).get("wins")
                losses = team.get("record", {}).get("losses")
                table.add_row(str(rank), name, str(wins), str(losses))
        self.console.print(table)

def main():
    parser = argparse.ArgumentParser(description="Object-Oriented Fleaflicker Dashboard")
    parser.add_argument("--league", required=True)
    parser.add_argument("--team")
    parser.add_argument("--sport", default="NBA")
    sub = parser.add_subparsers(dest="command", required=True)

    compare_parser = sub.add_parser("compare")
    compare_parser.add_argument("--position")

    scoreboard_parser = sub.add_parser("scoreboard")
    scoreboard_parser.add_argument("--scoring-period", type=int)

    sub.add_parser("standings")

    args = parser.parse_args()
    api = FleaflickerAPI(args.league, args.team, args.sport)
    dashboard = Dashboard(api)
    if args.command == "compare":
        dashboard.compare(position=args.position)
    elif args.command == "scoreboard":
        dashboard.show_scoreboard(scoring_period=args.scoring_period)
    elif args.command == "standings":
        dashboard.show_standings()

if __name__ == "__main__":
    main()
