# CLAUDE.md - Development Context

## Project Overview

**RL-Tracker** is a Rocket League Stats Display Application that scrapes player statistics from rocketleague.tracker.network and displays them in a polished desktop GUI.

### Purpose
- Monitor Rocket League player stats in real-time
- Display ranks, MMR, recent matches, and performance metrics
- Designed for Raspberry Pi deployment (can run on any system with Python)
- Updates stats periodically with configurable refresh intervals

## Architecture

```
┌─────────────────────┐
│ RL Tracker Website  │
└──────────┬──────────┘
           │
    [Playwright Scraper]
           │
           ▼
    ~/.cache/rl_stats.json
           │
    [PySide6 GUI App]
           │
           ▼
    Desktop Dashboard
```

### Tech Stack
- **Python 3.9+** (tested on 3.13)
- **Playwright** - Headless browser for web scraping
- **PySide6** - Qt-based GUI framework
- **PyYAML** - Configuration management
- **Requests** - HTTP library (for future enhancements)

## Project Structure

```
rl-tracker/
├── scraper.py           # Web scraper using Playwright
├── app.py               # PySide6 GUI application
├── config.yaml          # User configuration (username, platform, settings)
├── requirements.txt     # Python dependencies
├── .gitignore          # Git ignore patterns
├── README.md           # User-facing documentation
├── CLAUDE.md           # This file - dev context
└── assets/
    └── ranks/
        └── README.md    # Guide for adding rank badge images
```

## Key Files Explained

### scraper.py
- Uses Playwright to scrape RL Tracker pages (overview, matches, performance)
- Parses HTML to extract ranks, MMR, match history, performance stats
- Saves data to `~/.cache/rl_stats.json`
- Can be run standalone: `python scraper.py`

### app.py
- PySide6 GUI that reads from the cache file
- Displays stats in a dark-themed dashboard
- Auto-refreshes every N minutes (configurable)
- Features:
  - Current ranks for all playlists (1v1, 2v2, 3v3, etc.)
  - Recent match history with W/L and MMR changes
  - Performance metrics (goals, assists, saves, etc.)
  - Manual refresh button

### config.yaml
- User profile settings (platform: epic/steam/psn/xbl, username)
- Refresh interval (default: 10 minutes)
- Display settings (window size, theme)
- Cache path configuration

## Current Status

### ✅ Completed (Issue #1 - MVP)
- [x] Core scraper implementation with Playwright
- [x] PySide6 GUI with dark theme
- [x] Configuration system (YAML)
- [x] Local caching mechanism
- [x] Auto-refresh functionality
- [x] Recent matches display
- [x] Performance metrics display
- [x] Complete documentation (README.md)
- [x] Git repository setup
- [x] Initial commit and push to GitHub

### 📝 Known Issues
- **Python 3.13 Compatibility**: Original requirements.txt specified `PySide6==6.7.1` which doesn't support Python 3.13. Updated to `PySide6>=6.8.0` to support newer Python versions.

### 🔮 Future Enhancements (Not Yet Started)
- [ ] Add actual rank badge images to assets/ranks/
- [ ] Display rank badge images in GUI (currently text-only)
- [ ] Add MMR trend charts/graphs
- [ ] Voice assistant feedback for rank changes
- [ ] Systemd service for auto-start on Pi
- [ ] Settings UI panel (currently config file only)
- [ ] Notifications for rank ups/downs
- [ ] Multi-profile support
- [ ] Error handling improvements for site changes

## How to Run

### First Time Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium

# Configure your profile
# Edit config.yaml and set your username/platform
```

### Running the App
```bash
# Step 1: Scrape stats (run first, or when you want fresh data)
python scraper.py

# Step 2: Launch GUI
python app.py
```

The GUI will auto-refresh by re-reading the cache file every 10 minutes. To get truly fresh data, re-run `scraper.py`.

## Configuration

User must edit `config.yaml` before first use:

```yaml
profile:
  platform: "epic"      # Change to: epic, steam, psn, or xbl
  username: "Dragflex"  # Change to your RL Tracker username
```

## Important Notes for Future Development

1. **Web Scraping Fragility**: The scraper depends on RL Tracker's HTML structure. If the site changes, selectors in `scraper.py` may need updates.

2. **Rate Limiting**: No rate limiting implemented yet. Be mindful of scraping frequency to avoid being blocked.

3. **Error Handling**: Basic error handling exists but could be improved. If RL Tracker is down or username doesn't exist, errors may not be user-friendly.

4. **Cache Location**: Stats cached at `~/.cache/rl_stats.json` by default. On Windows this expands to `C:\Users\{user}\.cache\`.

5. **Headless Browser**: Playwright runs Chromium in headless mode. First run after `playwright install chromium` may take time.

6. **GUI Threading**: GUI runs on main thread. Auto-refresh reads from cache (not blocking), but if you integrate scraping into the GUI, use QThread to avoid freezing.

## Development Context

### Last Session Summary
- Implemented complete MVP (Issue #1)
- All core features working
- Fixed Python 3.13 compatibility issue with PySide6
- Committed and pushed to GitHub: `https://github.com/JuliusShade/RL-Tracker.git`
- Issue #1 was already closed when we tried to close it

### Repository Info
- **GitHub**: https://github.com/JuliusShade/RL-Tracker
- **Owner**: JuliusShade (Julius Shade)
- **Branch**: main
- **Last Commit**: adea88a - "feat: Implement Rocket League Stats Display App MVP"

### User's Environment
- OS: Windows (win32)
- Python: 3.13 (inferred from pip error)
- Using virtual environment in project directory
- Working Directory: `C:\Users\shade\OneDrive\Documents\DevProject\rl-tracker`

## Quick Start for New Claude Instance

If you're a new Claude instance picking this up:

1. **Read this file** to understand the project
2. **Check git status**: `git status` to see any uncommitted changes
3. **Review open issues**: `gh issue list` to see what needs work
4. **Test the app**: Try running `python scraper.py` and `python app.py` to ensure it works
5. **Check for TODOs**: Search codebase for `TODO` or `FIXME` comments

## Debugging Tips

### Scraper Issues
- Check if RL Tracker site is accessible: Visit URLs in config.yaml
- Verify username/platform are correct in config.yaml
- Run scraper with print statements to see what's being scraped
- Check if HTML selectors changed (use browser dev tools on RL Tracker)

### GUI Issues
- Ensure cache file exists: `~/.cache/rl_stats.json`
- Check cache file format is valid JSON
- Verify PySide6 installed: `pip show PySide6`
- Test with sample cache data if needed

### Installation Issues
- Python version: Must be 3.9+ (3.13 supported with updated requirements)
- Virtual environment recommended
- Windows users may need Visual C++ redistributables for some packages

## Contact & Links

- **Issue Tracker**: https://github.com/JuliusShade/RL-Tracker/issues
- **Rocket League Tracker**: https://rocketleague.tracker.network
- **Playwright Docs**: https://playwright.dev/python/
- **PySide6 Docs**: https://doc.qt.io/qtforpython-6/

---

**Last Updated**: 2025-11-11
**Status**: MVP Complete, Ready for Enhancements
