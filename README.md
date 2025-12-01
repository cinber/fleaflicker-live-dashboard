# Fleaflicker Live Dashboard

This repository contains Python scripts to create interactive dashboards and CLI tools for your Fleaflicker fantasy league. The tools default to **NBA**, but you can specify other sports.

## Installation
1. Clone the repository.  
2. Install dependencies using `pip install -r requirements.txt`.

## Usage

### Live TUI dashboard for your team
Run the TUI with your league and team IDs:

```
python fleaflicker_tui.py --league YOUR_LEAGUE_ID --team YOUR_TEAM_ID --sport NBA
```

Optionally specify `--position` to filter free agents by position (e.g., PG, SG, SF, PF, C).

### League scoreboard and standings
Use the league dashboard script to view the overall league scoreboard, standings, or compare your roster against free agents in a position:

```
# Show league scoreboard
python fleaflicker_league_dashboard.py scoreboard --league YOUR_LEAGUE_ID --sport NBA

# Show league standings
python fleaflicker_league_dashboard.py standings --league YOUR_LEAGUE_ID --sport NBA

# Compare your roster vs free agents by position
python fleaflicker_league_dashboard.py compare --league YOUR_LEAGUE_ID --team YOUR_TEAM_ID --sport NBA --position PG
```

## Features
- Live auto-updating dashboard every 10 seconds.  
- Displays your roster, free agents, and upgrade recommendations.  
- League scoreboard and standings view.  
- Hybrid scoring using 70% projections and 30% last-3-game averages.  
- Highlighted upgrade suggestions when free agents outperform your current roster.

## Files
- `fleaflicker_tui.py`: Live TUI dashboard for your team.  
- `fleaflicker_league_dashboard.py`: CLI/TUI for league scoreboard, standings, and comparisons.  
- `requirements.txt`: List of Python dependencies.
