"""
Rocket League Tracker Scraper
Uses Playwright to scrape stats from rocketleague.tracker.network
"""

import json
import os
import yaml
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


class RLTrackerScraper:
    """Scrapes Rocket League stats from tracker.network"""

    def __init__(self, config_path="config.yaml"):
        """Initialize scraper with configuration"""
        self.config = self._load_config(config_path)
        self.cache_path = Path(self.config['cache']['path']).expanduser()
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)

    def _load_config(self, config_path):
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Format URLs with profile info
        platform = config['profile']['platform']
        username = config['profile']['username']

        for key in config['urls']:
            config['urls'][key] = config['urls'][key].format(
                platform=platform,
                username=username
            )

        return config

    def scrape_overview(self, page):
        """Scrape overview page for rank information"""
        try:
            page.goto(self.config['urls']['overview'], timeout=60000)

            # Wait for the main content to load - look for the profile name/title
            page.wait_for_selector('h1, [class*="profile"]', timeout=15000)

            # Give the page additional time to fully render
            page.wait_for_timeout(3000)

            # Take screenshot for debugging
            page.screenshot(path="scraper_debug.png")

            stats = {}

            # Try to find rank cards/sections - these are usually in containers
            # Modern tracker.gg sites use data attributes and specific class patterns
            playlist_selectors = [
                '[class*="playlist"]',
                '[class*="rank-card"]',
                '[class*="mode"]',
                '[data-mode]',
                'div[class*="giant-stat"]',  # Tracker.gg specific
            ]

            playlists = []
            for selector in playlist_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    if elements and len(elements) > 0:
                        playlists = elements
                        print(f"Found {len(playlists)} elements with selector: {selector}")
                        break
                except:
                    continue

            if not playlists:
                print("No playlist elements found with any selector")
                # Try to extract any text that looks like rank data
                all_text = page.inner_text('body')
                print(f"Page body text (first 500 chars): {all_text[:500]}")
                return stats

            for i, playlist in enumerate(playlists):
                try:
                    # Get all text from this element
                    text = playlist.inner_text()

                    # Skip if too short or looks like navigation
                    if len(text) < 3 or 'Login' in text or 'Sign' in text:
                        continue

                    # Try to parse rank information from text
                    lines = [line.strip() for line in text.split('\n') if line.strip()]

                    if len(lines) >= 2:
                        # Common patterns: mode name, rank, MMR
                        playlist_name = lines[0]
                        rank_text = "Unranked"
                        mmr_val = 0.0

                        for line in lines[1:]:
                            # Look for rank names
                            if any(rank in line.lower() for rank in ['bronze', 'silver', 'gold', 'platinum', 'diamond', 'champion', 'grand champion', 'supersonic legend']):
                                rank_text = line
                            # Look for MMR (numeric value, possibly with comma)
                            elif line.replace(',', '').replace('.', '').isdigit():
                                mmr_val = float(line.replace(',', ''))

                        if playlist_name and (rank_text != "Unranked" or mmr_val > 0):
                            stats[playlist_name] = {
                                'rank': rank_text,
                                'mmr': mmr_val
                            }
                            print(f"Parsed: {playlist_name} - {rank_text} ({mmr_val} MMR)")

                except Exception as e:
                    print(f"Error parsing playlist {i}: {e}")
                    continue

            return stats

        except Exception as e:
            print(f"Error scraping overview: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def scrape_matches(self, page):
        """Scrape recent match history"""
        try:
            page.goto(self.config['urls']['matches'], timeout=60000)
            page.wait_for_selector('h1, [class*="profile"]', timeout=15000)
            page.wait_for_timeout(3000)

            matches = []

            # Look for match/game history containers
            match_selectors = [
                '[class*="match"]',
                '[class*="game"]',
                '[class*="session"]',
                'tr[class*="row"]'
            ]

            match_elements = []
            for selector in match_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    if elements and len(elements) >= 3:  # At least a few matches
                        match_elements = elements[:10]  # Limit to 10
                        print(f"Found {len(elements)} match elements with selector: {selector}")
                        break
                except:
                    continue

            if not match_elements:
                print("No match elements found")
                return matches

            for i, match in enumerate(match_elements):
                try:
                    text = match.inner_text()
                    lines = [line.strip() for line in text.split('\n') if line.strip()]

                    # Skip navigation/header elements
                    if len(lines) < 2:
                        continue

                    # Try to parse match info
                    result = "Unknown"
                    playlist = "Unknown"
                    mmr_change = "0"

                    for line in lines:
                        if any(w in line.lower() for w in ['win', 'victory', 'defeat', 'loss']):
                            result = line
                        elif any(w in line.lower() for w in ['doubles', 'duel', 'standard', 'ranked']):
                            playlist = line
                        elif '+' in line or '-' in line:
                            if any(c.isdigit() for c in line):
                                mmr_change = line

                    if result != "Unknown" or playlist != "Unknown":
                        matches.append({
                            'result': result,
                            'playlist': playlist,
                            'mmr_change': mmr_change
                        })

                except Exception as e:
                    print(f"Error parsing match {i}: {e}")
                    continue

            return matches

        except Exception as e:
            print(f"Error scraping matches: {e}")
            import traceback
            traceback.print_exc()
            return []

    def scrape_performance(self, page):
        """Scrape performance metrics"""
        try:
            page.goto(self.config['urls']['performance'], timeout=60000)
            page.wait_for_selector('h1, [class*="profile"]', timeout=15000)
            page.wait_for_timeout(3000)

            performance = {}

            # Look for stat containers
            stat_selectors = [
                '[class*="stat"]',
                '[class*="metric"]',
                'div[class*="giant"]'
            ]

            stat_elements = []
            for selector in stat_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    if elements and len(elements) >= 3:
                        stat_elements = elements
                        print(f"Found {len(elements)} stat elements with selector: {selector}")
                        break
                except:
                    continue

            if not stat_elements:
                print("No performance stat elements found")
                return performance

            for i, stat in enumerate(stat_elements):
                try:
                    text = stat.inner_text()
                    lines = [line.strip() for line in text.split('\n') if line.strip()]

                    # Skip if too short
                    if len(lines) < 2:
                        continue

                    # Try to pair label with value
                    for j in range(len(lines) - 1):
                        label = lines[j]
                        value = lines[j + 1]

                        # Skip navigation items
                        if any(skip in label.lower() for skip in ['login', 'sign', 'menu', 'nav']):
                            continue

                        # If we have a label and numeric-ish value, store it
                        if len(label) > 1 and (value.replace(',', '').replace('.', '').replace('%', '').isdigit() or any(c.isdigit() for c in value)):
                            performance[label] = value

                except Exception as e:
                    print(f"Error parsing stat {i}: {e}")
                    continue

            return performance

        except Exception as e:
            print(f"Error scraping performance: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def scrape_all(self):
        """Scrape all stats and save to cache"""
        print("Starting scraper...")

        with sync_playwright() as p:
            try:
                # Launch browser with options to avoid detection
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                    ]
                )

                # Create context with realistic settings
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )

                page = context.new_page()

                # Remove webdriver property
                page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """)

                # Scrape all pages
                print("Scraping overview...")
                overview = self.scrape_overview(page)

                print("Scraping matches...")
                matches = self.scrape_matches(page)

                print("Scraping performance...")
                performance = self.scrape_performance(page)

                # Close browser
                browser.close()

                # Combine all data
                data = {
                    'timestamp': datetime.now().isoformat(),
                    'overview': overview,
                    'recent_matches': matches,
                    'performance': performance
                }

                # Save to cache
                with open(self.cache_path, 'w') as f:
                    json.dump(data, f, indent=2)

                print(f"Stats saved to {self.cache_path}")
                return data

            except Exception as e:
                print(f"Error during scraping: {e}")
                import traceback
                traceback.print_exc()
                return None


def main():
    """Main entry point for scraper"""
    scraper = RLTrackerScraper()
    data = scraper.scrape_all()

    if data:
        print("\n=== Scraped Stats ===")
        print(json.dumps(data, indent=2))
    else:
        print("Failed to scrape stats")


if __name__ == "__main__":
    main()
