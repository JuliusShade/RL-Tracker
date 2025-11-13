# 🚀 Rocket League Stats Display App

A Raspberry Pi-friendly Python application that displays Rocket League Tracker profile data in a polished desktop dashboard.

The app uses a two-step workflow: first download the HTML from RL Tracker, then parse it offline to extract stats. This avoids Cloudflare bot detection and provides reliable data extraction.

## 📊 Architecture Overview

```text
┌────────────────────────┐
│  RL Tracker Website    │ (overview page)
└───────────┬────────────┘
            │
    [Chrome CDP Scraper]  (saves HTML)
            │
            ▼
    data/html/overview.html
            │
    [BeautifulSoup Parser]  (extracts data)
            │
            ▼
    rl_stats.json (cache)
            │
    [PySide6 GUI]
            │
            ▼
  Beautiful Dashboard w/ Live Stats
```

## 🔧 Technical Details

### Language & Frameworks
- **Python 3.9+** - core logic and runtime (tested on 3.13)
- **Playwright** - connects to real Chrome browser to download HTML
- **BeautifulSoup4** - offline HTML parsing (reliable, no Cloudflare issues)
- **PySide6 (Qt for Python)** - GUI rendering with dark theme
- **YAML / JSON** - configuration and caching

### Key Modules
- **`scraper_cdp_auto.py`** - connects to Chrome via CDP to save HTML from overview page
- **`parser.py`** - uses BeautifulSoup to extract ranks, sessions, lifetime stats from saved HTML
- **`app.py`** - builds responsive PySide6 GUI with stats dashboard
- **`activity_map.py`** - creates GitHub-style activity heatmap showing match frequency
- **`rank_map.py`** - maps rank text to icon file paths (e.g., "Champion III" → Champion3_rank_icon.webp)
- **`assets/ranks/`** - stores rank icon images (Bronze → Supersonic Legend)
- **`config.yaml`** - profile settings and display configuration

## 📁 Project Structure

```bash
rl-tracker/
├── scraper_cdp_auto.py        # Chrome CDP HTML downloader
├── parser.py                  # BeautifulSoup HTML parser
├── app.py                     # PySide6 GUI renderer
├── activity_map.py            # Play activity heatmap widget
├── rank_map.py                # Rank icon mapping utilities
├── data/
│   └── html/
│       └── overview.html      # Saved HTML (auto-generated)
├── assets/
│   └── ranks/*.webp           # Rank badges (Champion1, Diamond2, etc.)
├── config.yaml                # Profile and display settings
├── rl_stats.json              # Parsed stats cache (auto-generated)
├── requirements.txt           # Dependencies
├── README.md                  # This file
└── CLAUDE.md                  # Development context
```

## 🔨 Installation

### Prerequisites
- Python 3.9 or higher (tested on Python 3.13)
- Microsoft Edge or Google Chrome browser
- pip (Python package manager)

### Setup Steps

1. **Clone the repository**
```bash
git clone https://github.com/JuliusShade/RL-Tracker.git
cd RL-Tracker
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Install Playwright browser**
```bash
playwright install chromium
```

4. **Configure your profile**
Edit `config.yaml` and set your profile information:
```yaml
profile:
  platform: "epic"  # Options: epic, steam, psn, xbl
  username: "YourUsername"
```

## 🎮 Usage

### Recommended Workflow (Best for Avoiding Cloudflare)

The easiest and most reliable way to use the app is to keep your RL Tracker page open in Edge:

#### Step 1: Start Edge with Remote Debugging

**Close ALL Edge windows first**, then open PowerShell and run:

**Windows**:
```powershell
Start-Process "msedge.exe" -ArgumentList "--remote-debugging-port=9222"
```

**Mac/Linux**:
```bash
google-chrome --remote-debugging-port=9222 &
```

This opens Edge with your **normal profile** (cookies, history, extensions intact) - no Cloudflare detection!

#### Step 2: Open RL Tracker Page

In that Edge window, navigate to your profile:
```
https://rocketleague.tracker.network/rocket-league/profile/{platform}/{username}/overview
```

Replace `{platform}` with your platform (epic/steam/psn/xbl) and `{username}` with your username.

**Keep this tab open!** RL Tracker auto-refreshes stats every 5 minutes.

#### Step 3: Launch the App

```bash
python app.py
```

The GUI will:
- Display current ranks with rank icons
- Show lifetime stats (wins, goals, assists, saves, MVPs, etc.)
- Display play activity heatmap (last 30 days)
- Show recent gaming sessions with match counts
- Display stats breakdown pie chart

#### Step 4: Refresh Stats

Click the **Refresh** button in the app anytime to update stats. The app will:
- ✅ Detect your open RL Tracker tab
- ✅ Grab the HTML from that tab (instant, no navigation!)
- ✅ Parse the data and update the display
- ✅ No Cloudflare issues (using your real browser session)

**Note**: The RL Tracker site auto-refreshes every 5 minutes, or you can manually refresh the page in your browser before clicking the app's refresh button.

### Alternative: Automatic Navigation (Less Reliable)

If you don't have the page open, the app will attempt to navigate automatically, but this may trigger Cloudflare verification. It's recommended to keep the page open as described above.

## ✨ Features

### Data Extraction
- 🏆 **All ranks and MMR** from all playlists (1v1, 2v2, 3v3, Extra Modes)
- 📊 **Lifetime statistics** - wins, goals, assists, saves, shots, MVPs, goal shot ratio
- 🕒 **Gaming sessions** - recent play sessions with match counts and stats
- 📈 **Activity heatmap** - GitHub-style visualization of matches over last 30 days
- 📉 **Match stats breakdown** - pie chart of goals/assists/saves distribution

### Display
- 🎨 **Polished dark theme** optimized for 7" Raspberry Pi touchscreen (800x480)
- 🖼️ **Rank icon display** - visual rank badges (Champion3_rank_icon.webp, etc.)
- 📊 **Compact layout** - all content fits on one screen, no scrolling
- 🔄 **Auto-refresh** - updates display every 10 minutes
- ⚙️ **Configurable** - theme, size, refresh interval via config.yaml

### Technical
- 🛡️ **Cloudflare bypass** - uses your real browser with existing tabs, zero automation detection
- 💾 **Offline parsing** - BeautifulSoup extracts data from HTML
- 📦 **Smart tab detection** - automatically finds and reuses open RL Tracker tabs
- 📂 **Local caching** - stores data in project directory
- 🔧 **Config-driven** - easy customization via YAML
- 🔌 **Chrome DevTools Protocol** - connects to browser without automation flags

## ⚙️ Configuration

Edit `config.yaml` to customize:

```yaml
# Change your profile
profile:
  platform: "epic"      # Options: epic, steam, psn, xbl
  username: "YourUsername"

# Adjust refresh rate
refresh:
  interval_minutes: 10

# Cache location (relative to project root)
cache:
  path: "rl_stats.json"

# Change display settings
display:
  window_width: 800
  window_height: 480    # Optimized for 7" Raspberry Pi touchscreen
  theme: "dark"         # Options: dark, light
```

## 📊 Data Structure

The parser extracts and caches the following data structure:

```json
{
  "timestamp": "2025-11-12T21:05:07",
  "overview": {
    "Ranked Duel 1v1": {
      "rank": "Diamond I Div II",
      "mmr": 823
    },
    "Ranked Doubles 2v2": {
      "rank": "Champion III Div I",
      "mmr": 1308
    },
    "__lifetime__": {
      "Wins": "2,260",
      "Goals": "5,785",
      "Assists": "2,292",
      "Saves": "3,656",
      "Shots": "11,940",
      "MVPs": "897",
      "Goal Shot Ratio": "48.5%"
    }
  },
  "sessions": [
    {
      "time_ago": "22 hours ago",
      "date": "2025-11-12",
      "wins": 12,
      "matches": [
        {
          "count": 49,
          "playlist": "Ranked Standard 3v3",
          "mmr": 1096
        }
      ],
      "goals": 22,
      "assists": 13,
      "saves": 249,
      "mvp_count": 6
    }
  ],
  "activity_heatmap": [
    {
      "date": "2025-11-12",
      "count": 122
    }
  ]
}
```

## 🥧 Deployment Notes (Raspberry Pi)

### Install System Dependencies
```bash
sudo apt update
sudo apt install python3-pip chromium-browser -y
```

### Install Python Dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### Configure for Pi Display
The app is optimized for a 7" touchscreen (800x480) by default. The layout is compact with improved text rendering - no cropping or overflow issues.

### Run the App
```bash
# Start browser with debugging
chromium-browser --remote-debugging-port=9222 --user-data-dir=/tmp/chrome_debug &

# Download HTML and parse
python scraper_cdp_auto.py

# Launch GUI
python app.py
```

### Autostart at Boot

Create a startup script:
```bash
nano ~/start_rl_tracker.sh
```

Add:
```bash
#!/bin/bash
cd /home/pi/RL-Tracker
chromium-browser --remote-debugging-port=9222 --user-data-dir=/tmp/chrome_debug &
sleep 5
python3 app.py
```

Make it executable and add to autostart:
```bash
chmod +x ~/start_rl_tracker.sh
# Add to ~/.config/autostart or crontab
```

For periodic scraping:
```bash
crontab -e
```

Add:
```bash
*/30 * * * * cd /home/pi/RL-Tracker && /usr/bin/python3 scraper_cdp_auto.py
```

## 🔧 Troubleshooting

### Scraper Issues
- **"Could not connect to Edge"**: Make sure you started the browser with `--remote-debugging-port=9222`
- **Cloudflare challenge appears**: Complete the verification manually in the browser - the scraper will detect when it's cleared and continue
- **No HTML saved**: Check that the browser is accessible at `http://localhost:9222`
- **Stats not loading**: Verify your username/platform in config.yaml

### Parser Issues
- **"Could not load overview.html"**: Run `scraper_cdp_auto.py` first to download the HTML
- **No lifetime stats**: The overview page may not be showing lifetime stats - check the HTML file
- **No sessions found**: The parser may need selector updates if RL Tracker changed their layout

### GUI Issues
- **App won't start**: Ensure PySide6 is installed: `pip install PySide6>=6.8.0`
- **No stats shown**: Run `scraper_cdp_auto.py` then `parser.py` to populate the cache
- **Text is cropped**: Update to latest version - text cropping issues have been fixed
- **Rank icons not showing**: Add rank icon files to `assets/ranks/` (e.g., `Champion3_rank_icon.webp`)
- **Wrong rank icon**: Rank mapping has been fixed - update to latest version

## 🎯 Recent Updates

### Latest (November 2025)

✅ **Smart Tab Detection** (NEW!):
- App now detects and reuses existing RL Tracker tabs in your browser
- No more navigation or Cloudflare challenges - just grab HTML from open tab
- Instant refresh when using an already-open page
- Site auto-refreshes every 5 minutes anyway
- Perfect for continuous monitoring

✅ **Zero Automation Detection**:
- Uses your real browser profile (cookies, history, extensions)
- No automation flags or anti-detection needed
- Chrome DevTools Protocol connects to existing browser
- Looks 100% like normal browsing to Cloudflare

✅ **Parser-Based Workflow**:
- Switched from direct Playwright scraping to HTML download + offline parsing
- Uses BeautifulSoup for reliable data extraction
- Only needs overview page HTML (no matches/performance pages required)

✅ **Lifetime Stats**:
- Added comprehensive lifetime statistics display
- Extracts wins, goals, assists, saves, shots, MVPs, goal shot ratio
- Displays in dedicated stats section

✅ **Fixed Rank Icon Mapping**:
- Fixed bug where "Champion III Div I" showed Champion I icon
- Now correctly extracts rank tier from rank name (not division)
- Uses regex to match rank patterns precisely

✅ **UI Improvements**:
- Fixed text cropping in all sections (ranks, sessions, stats)
- Resized pie chart to fit properly
- Added word wrap to prevent text overflow
- Improved label sizing and spacing
- Compact layout optimized for 800x480 displays

## 📋 Next Steps

- [ ] Add more rank badge images to `assets/ranks/` directory
- [ ] Add MMR trend charts over time
- [ ] Add systemd service for automatic startup
- [ ] Add persistent settings UI (currently config file only)
- [ ] Add notifications for rank changes
- [ ] Multi-profile support (track multiple players)

## 📄 License

MIT License - feel free to use and modify

## 👤 Author

Julius Shade
November 2025

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

**Note**: This app relies on scraping RL Tracker's website structure. If the site changes significantly, the parser selectors in `parser.py` may need updates. The HTML-based approach makes debugging and updating selectors much easier than live scraping.
