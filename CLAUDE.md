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
    rl_stats.json (project root)
           │
    [PySide6 GUI App]
           │
           ▼
    Desktop Dashboard (800x480 Pi-optimized)
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
├── activity_map.py      # Play activity heatmap widget
├── rank_map.py          # Rank icon mapping utilities
├── config.yaml          # User configuration (username, platform, settings)
├── rl_stats.json        # Cached stats (auto-generated)
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
- Parses HTML to extract ranks, MMR, match history with dates, performance stats
- Includes anti-Cloudflare detection measures
- Extended timeouts (60s page load, 20s selectors, 5s render delay)
- Date parsing for relative dates ("2 days ago") and absolute dates
- Saves data to `rl_stats.json` in project root
- Can be run standalone: `python scraper.py`

### app.py
- PySide6 GUI that reads from the cache file
- Displays stats in a dark-themed dashboard optimized for 7" Pi display (800x480)
- Compact layout with NO scrollbars - all content fits on one screen
- Auto-refreshes every N minutes (configurable)
- Features:
  - Current ranks for all playlists with rank icons (or emoji fallback)
  - Play activity heatmap (GitHub-style, last 30 days)
  - Recent match history (last 3 matches) with W/L and MMR changes
  - Performance metrics (top 4 stats)
  - Manual refresh button

### activity_map.py
- Creates GitHub-style activity heatmap widget
- Visualizes match frequency over last 30 days
- Color-coded squares (dark gray = no activity, bright orange = high activity)
- Tooltips showing date and match count
- Parses match dates from scraper data

### rank_map.py
- Maps rank text to icon file paths
- Normalizes rank names (e.g., "Champion III Division II" → "champion_iii")
- Handles multiple rank formats and divisions
- Falls back to unranked.png or base rank if specific division not found

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

### ✅ Completed (Issue #2 - Fix Scraper & Add Rank Icons)
- [x] Fixed Playwright scraper to bypass Cloudflare bot detection
- [x] Improved scraper with anti-detection measures (user agent, viewport, init scripts)
- [x] Updated selectors to handle client-side rendered content
- [x] Added extended timeouts and wait strategies (60s page load, 15s selector wait, 3s render delay)
- [x] Created rank_map.py module for rank-to-icon mapping
- [x] Updated app.py to display rank icons alongside stats
- [x] Added emoji fallback (🏆) when rank icons not found
- [x] Improved error handling and debugging (screenshots, traceback)

### ✅ Completed (Issue #3 - Fix Cache Path, Integrate Rank Images, Add Activity Heatmap)
- [x] Changed cache path from `~/.cache/rl_stats.json` to project root `rl_stats.json`
- [x] Updated both scraper.py and app.py to use project-relative cache path
- [x] Improved scraper selectors for better match/performance parsing
- [x] Added date parsing (absolute and relative) to match data
- [x] Increased match limit to 20 for better activity tracking
- [x] Created activity_map.py module with GitHub-style heatmap widget
- [x] Integrated activity heatmap into app.py dashboard
- [x] Optimized entire layout for 7" Raspberry Pi touchscreen (800x480)
- [x] Removed scrollbars - all content fits on one screen
- [x] Compacted all UI elements (fonts, spacing, margins)
- [x] Rank icons now display at 32px size (down from 48px)
- [x] Recent matches limited to top 3 for space efficiency
- [x] Performance stats limited to top 4 in horizontal layout
- [x] Updated config.yaml to default to 800x480 dimensions
- [x] Created sample rl_stats.json for testing
- [x] Completely rewrote README.md with updated instructions
- [x] Updated CLAUDE.md with Issue #3 completion

### 📝 Known Issues
- **Python 3.13 Compatibility**: Original requirements.txt specified `PySide6==6.7.1` which doesn't support Python 3.13. Updated to `PySide6>=6.8.0` to support newer Python versions. ✅ Resolved
- **Cloudflare Protection**: The scraper now includes anti-bot detection measures, but Cloudflare may still occasionally block requests. If scraping fails, try running again after a few minutes. This is an ongoing challenge with web scraping.
- **Rank Icons**: The assets/ranks/ directory is currently empty. Users can add their own rank icon PNGs following the naming convention (e.g., `champion_i.png`, `diamond_ii.png`). The app will show emoji placeholders (🏆) until icons are added.
- **Scraper Parsing**: The scraper may occasionally fail to parse match/performance data if the RL Tracker site structure changes. Debug screenshots (scraper_debug.png) are saved for troubleshooting. Sample data provided in rl_stats.json for GUI testing.
- **Cache Location**: Changed from user cache directory to project root. ✅ Resolved in Issue #3

### 🔮 Future Enhancements (Not Yet Started)
- [ ] Add actual rank badge PNG images to assets/ranks/
- [ ] Add MMR trend charts/graphs over time
- [ ] Voice assistant feedback for rank changes
- [ ] Systemd service for auto-start on Pi
- [ ] Settings UI panel (currently config file only)
- [ ] Notifications for rank ups/downs
- [ ] Multi-profile support (track multiple players)
- [ ] Error handling improvements for site changes
- [ ] API integration (if RL Tracker offers one in the future)

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

**Note**: A sample `rl_stats.json` file is included for testing the GUI without scraping.

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

4. **Cache Location**: Stats now cached at `rl_stats.json` in the project root directory (changed in Issue #3). This makes deployment easier and keeps all app data together.

5. **Headless Browser**: Playwright runs Chromium in headless mode. First run after `playwright install chromium` may take time.

6. **Pi Display**: The layout is optimized for 800x480 (7" touchscreen). For other resolutions, adjust `window_width` and `window_height` in config.yaml. The window will be fixed-size when set to 800x480 to prevent accidental resizing.

6. **GUI Threading**: GUI runs on main thread. Auto-refresh reads from cache (not blocking), but if you integrate scraping into the GUI, use QThread to avoid freezing.

## Development Context

### Last Session Summary
- Completed Issue #3: Fix Cache Save Path, Integrate Rank Images, and Add Play Activity Heatmap
- Changed cache from `~/.cache/rl_stats.json` to project root `rl_stats.json`
- Created activity_map.py module for GitHub-style play activity heatmap
- Added date parsing (absolute and relative) to match scraping
- Optimized entire layout for 7" Raspberry Pi touchscreen (800x480)
- Made UI compact with no scrollbars - all content fits on one screen
- Integrated rank icons at 32px size (compact)
- Integrated activity heatmap widget into dashboard
- Compacted all sections (ranks, matches, performance) for space efficiency
- Updated config.yaml to default to Pi display dimensions
- Created sample rl_stats.json for testing
- Completely rewrote README.md with comprehensive instructions
- Updated CLAUDE.md with Issue #3 completion status
- Ready to commit and push changes, then close Issue #3

### Repository Info
- **GitHub**: https://github.com/JuliusShade/RL-Tracker
- **Owner**: JuliusShade (Julius Shade)
- **Branch**: main
- **Last Commit**: adea88a - "feat: Implement Rocket League Stats Display App MVP" (about to be updated)

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
**Status**: Issue #3 Complete - Pi Display Optimized, Ready for Deployment
