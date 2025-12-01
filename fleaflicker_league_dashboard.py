#!/usr/bin/env python3
import requests
import argparse
from statistics import mean
from rich.console import Console
from rich.table import Table

API_BASE = "https://www.fleaflicker.com/api"

def fetch_roster(league_id, team_id, sport):
    url = f"{API_BASE}/FetchRoster"
    params = {"league_id": league_id, "team_id": team_id, "sport": sport}
    r = requests.get(url, params=params)
    r.raise_for_status()
    return r.json()

def fetch_free_agents(league_id, sport, position=None):
    url = f"{API_BASE}/FetchPlayerListing"
    params = {"league_id": league_id, "sport": sport, "filter.free_agent_only": "true", "sort": "SORT_PROJECTIONS"}
    if position:
        params["filter.position.eligibility"] = position
    r = requests.get(url, params=params)
    r.raise_for_status()
    return r.json()

def fetch_league_scoreboard(league_id, sport, scoring_period=None):
    url = f"{API_BASE}/FetchLeagueScoreboard"
    params = {"league_id": league_id, "sport": sport}
    if scoring_period:
        params["scoring_period"] = scoring_period
    r = requests.get(url, params=params)
    r.raise_for_status()
    return r.json()

def fetch_league_standings(league_id, sport):
    url = f"{API_BASE}/FetchLeagueStandings"
    params = {"league_id": league_id, "sport": sport}
    r = requests.get(url, params=params)
    r.raise_for_status()
    return r.json()

def extract_roster_players(roster_json):
    players = []
    for group in roster_json.get("groups", []):
        for slot in group.get("slots", []):
            lp = slot.get("league_player")
            if lp:
                players.append(lp)
    return players

def print_scoreboard(scoreboard):
    console = Console()
    table = Table(title="League Scoreboard")
    table.add_column("Matchup")
    table.add_column("Home Team")
    table.add_column("Home Score")
    table.add_column("Away Team")
    table.add_column("Away Score")
    for card in scoreboard.get("matchups", []):
        home = card.get("home", {})
        away = card.get("away", {})
        table.add_row(
            f"{home.get('team', {}).get('name', '')} vs {away.get('team', {}).get('name', '')}",
            home.get('team', {}).get('name', ''),
            str(home.get('score', {}).get('value', '')),
            away.get('team', {}).get('name', ''),
            str(away.get('score', {}).get('value', ''))
        )
    console.print(table)

def print_standings(standings):
    console = Console()
    table = Table(title="League Standings")
    table.add_column("Rank")
    table.add_column("Team")
    table.add_column("Wins")
    table.add_column("Losses")
    table.add_column("Ties")
    for division in standings.get("divisions", []):
        for team in division.get("teams", []):
            record = team.get("recordOverall", {})
            table.add_row(
                str(team.get("rank", '')),
                team.get("name", ''),
                str(record.get("wins", '')),
                str(record.get("losses", '')),
                str(record.get("ties", ''))
            )
    console.print(table)

def main():
    parser = argparse.ArgumentParser(description="Fleaflicker league dashboard CLI")
    subparsers = parser.add_subparsers(dest="command")
    roster_cmd = subparsers.add_parser("roster")
    roster_cmd.add_argument("--league", required=True)
    roster_cmd.add_argument("--team", required=True)
    roster_cmd.add_argument("--sport", default="NFL")
    roster_cmd.add_argument("--position", required=False)

    fa_cmd = subparsers.add_parser("free-agents")
    fa_cmd.add_argument("--league", required=True)
    fa_cmd.add_argument("--sport", default="NFL")
    fa_cmd.add_argument("--position", required=False)

    compare_cmd = subparsers.add_parser("compare")
    compare_cmd.add_argument("--league", required=True)
    compare_cmd.add_argument("--team", required=True)
    compare_cmd.add_argument("--sport", default="NFL")
    compare_cmd.add_argument("--position", required=False)

    scoreboard_cmd = subparsers.add_parser("scoreboard")
    scoreboard_cmd.add_argument("--league", required=True)
    scoreboard_cmd.add_argument("--sport", default="NFL")
    scoreboard_cmd.add_argument("--scoring-period", type=int, required=False)

    standings_cmd = subparsers.add_parser("standings")
    standings_cmd.add_argument("--league", required=True)
    standings_cmd.add_argument("--sport", default="NFL")

    args = parser.parse_args()

    if args.command == "scoreboard":
        data = fetch_league_scoreboard(args.league, args.sport, args.scoring_period)
        print_scoreboard(data)
    elif args.command == "standings":
        data = fetch_league_standings(args.league, args.sport)
        print_standings(data)
    elif args.command == "roster":
        roster = fetch_roster(args.league, args.team, args.sport)
        players = extract_roster_players(roster)
        console = Console()
        table = Table(title="Roster")
        table.add_column("Name")
        table.add_column("Position")
        table.add_column("Team")
        for p in players:
            pro = p["pro_player"]
            table.add_row(pro.get("name_full",""), pro.get("position",""), pro.get("pro_team_abbreviation",""))
        console.print(table)
    elif args.command == "free-agents":
        fa_json = fetch_free_agents(args.league, args.sport, args.position)
        players = fa_json.get("players", [])
        console = Console()
        table = Table(title="Free Agents")
        table.add_column("Name")
        table.add_column("Position")
        table.add_column("Team")
        for p in players:
            pro = p["pro_player"]
            table.add_row(pro.get("name_full",""), pro.get("position",""), pro.get("pro_team_abbreviation",""))
        console.print(table)
    elif args.command == "compare":
        roster = fetch_roster(args.league, args.team, args.sport)
        fa_json = fetch_free_agents(args.league, args.sport, args.position)
        roster_players = extract_roster_players(roster)
        fa_players = fa_json.get("players", [])
        console = Console()
        table = Table(title="Comparison between roster and free agents")
        table.add_column("Roster Player")
        table.add_column("Position")
        table.add_column("Free Agent Upgrade")
        for rp in roster_players:
            pos = rp["pro_player"]["position"]
            rp_name = rp["pro_player"]["name_full"]
            upgrade = next((fa for fa in fa_players if fa["pro_player"]["position"]==pos), None)
            upgrade_name = upgrade["pro_player"]["name_full"] if upgrade else ""
            table.add_row(rp_name, pos, upgrade_name)
        console.print(table)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
