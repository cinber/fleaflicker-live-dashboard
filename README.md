# Fleaflicker Live Dashboard

This repository contains Python scripts to create interactive dashboards and CLI tools for your Fleaflicker fantasy league. The tools default to **NBA**, but you can specify other sports.

## Installation
1. Clone the repository.
2. Install in editable mode (preferred for local dev):
   ```
   pip install -e .
   ```
   Or install the raw dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage (single app)

All commands now live behind one entry point:
- Module: `python -m fleaflicker_dashboard ...`
- Console script (after install): `fleaflicker-dashboard ...`

### Live TUI dashboard for your team
Launch the Textual UI:

```
python -m fleaflicker_dashboard tui --league YOUR_LEAGUE_ID --team YOUR_TEAM_ID --sport NBA
```

Optionally specify `--position` to filter free agents by position (e.g., PG, SG, SF, PF, C).

### League scoreboard and standings
Use the league dashboard script to view the overall league scoreboard, standings, or compare your roster against free agents in a position:

```
# Show league scoreboard
python -m fleaflicker_dashboard league scoreboard --league YOUR_LEAGUE_ID --sport NBA

# Show league standings
python -m fleaflicker_dashboard league standings --league YOUR_LEAGUE_ID --sport NBA

# Compare your roster vs free agents by position
python -m fleaflicker_dashboard league compare --league YOUR_LEAGUE_ID --team YOUR_TEAM_ID --sport NBA --position PG
```

## Features
- Live auto-updating dashboard every 10 seconds.  
- Displays your roster, free agents, and upgrade recommendations.  
- League scoreboard and standings view.  
- Hybrid scoring using 70% projections and 30% last-3-game averages.  
- Highlighted upgrade suggestions when free agents outperform your current roster.

## Project layout
- `fleaflicker_dashboard/`: Shared package with the Fleaflicker API client, player helpers, table builders, reusable dashboard logic, and unified CLI (`python -m fleaflicker_dashboard`).  
- `requirements.txt`: Synced list of Python dependencies.
- `pyproject.toml`: Package metadata, console script entry point, and tooling config (ruff, black, mypy).
