# Fleaflicker Live Dashboard  
This repository contains a Python script `fleaflicker_tui.py` that creates a live auto-updating dashboard for your Fleaflicker fantasy team. The dashboard refreshes every 10 seconds, showing your roster, free agents, and upgrade recommendations based on projections and recent performance.  

## Installation  
1. Clone the repository.  
2. Install dependencies using `pip install -r requirements.txt`.  

## Usage  
Run the TUI with your league and team IDs:  
```
python fleaflicker_tui.py --league YOUR_LEAGUE_ID --team YOUR_TEAM_ID --sport NFL
```  
Optionally specify `--position` to filter free agents by position (e.g., QB, RB).  

## Features  
- Live auto-updating dashboard every 10 seconds.  
- Displays your roster, free agents, and upgrade recommendations.  
- Hybrid scoring using 70% projections and 30% last-3 games average.  
- Highlighted upgrade suggestions when free agents outperform your current roster.  

## Files  
- `fleaflicker_tui.py`: Main TUI script.  
- `requirements.txt`: List of Python dependencies.
