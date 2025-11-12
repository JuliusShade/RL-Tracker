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
            page.goto(self.config['urls']['overview'], timeout=30000)
            page.wait_for_load_state('networkidle', timeout=30000)

            stats = {}

            # Wait for playlist stats to load
            page.wait_for_selector('.playlist', timeout=10000)

            # Get all playlists
            playlists = page.query_selector_all('.playlist')

            for playlist in playlists:
                try:
                    # Get playlist name
                    name_elem = playlist.query_selector('.playlist__name')
                    if not name_elem:
                        continue

                    playlist_name = name_elem.inner_text().strip()

                    # Get rank
                    rank_elem = playlist.query_selector('.rank__name')
                    rank = rank_elem.inner_text().strip() if rank_elem else "Unranked"

                    # Get division
                    div_elem = playlist.query_selector('.rank__division')
                    division = div_elem.inner_text().strip() if div_elem else ""

                    # Get MMR
                    mmr_elem = playlist.query_selector('.rank__mmr')
                    mmr = mmr_elem.inner_text().strip() if mmr_elem else "0"

                    # Clean up MMR (remove non-numeric characters except decimals)
                    mmr_clean = ''.join(c for c in mmr if c.isdigit() or c == '.')

                    full_rank = f"{rank} {division}".strip()

                    stats[playlist_name] = {
                        'rank': full_rank,
                        'mmr': float(mmr_clean) if mmr_clean else 0.0
                    }
                except Exception as e:
                    print(f"Error parsing playlist: {e}")
                    continue

            return stats

        except Exception as e:
            print(f"Error scraping overview: {e}")
            return {}

    def scrape_matches(self, page):
        """Scrape recent match history"""
        try:
            page.goto(self.config['urls']['matches'], timeout=30000)
            page.wait_for_load_state('networkidle', timeout=30000)

            matches = []

            # Wait for matches to load
            page.wait_for_selector('.match', timeout=10000)

            # Get recent matches (limit to 10)
            match_elements = page.query_selector_all('.match')[:10]

            for match in match_elements:
                try:
                    # Get result (Win/Loss)
                    result_elem = match.query_selector('.match__result')
                    result = result_elem.inner_text().strip() if result_elem else "Unknown"

                    # Get playlist
                    playlist_elem = match.query_selector('.match__playlist')
                    playlist = playlist_elem.inner_text().strip() if playlist_elem else "Unknown"

                    # Get MMR change
                    mmr_elem = match.query_selector('.match__mmr-change')
                    mmr_change = mmr_elem.inner_text().strip() if mmr_elem else "0"

                    matches.append({
                        'result': result,
                        'playlist': playlist,
                        'mmr_change': mmr_change
                    })
                except Exception as e:
                    print(f"Error parsing match: {e}")
                    continue

            return matches

        except Exception as e:
            print(f"Error scraping matches: {e}")
            return []

    def scrape_performance(self, page):
        """Scrape performance metrics"""
        try:
            page.goto(self.config['urls']['performance'], timeout=30000)
            page.wait_for_load_state('networkidle', timeout=30000)

            performance = {}

            # Wait for stats to load
            page.wait_for_selector('.stat', timeout=10000)

            # Get performance stats
            stats = page.query_selector_all('.stat')

            for stat in stats:
                try:
                    label_elem = stat.query_selector('.stat__label')
                    value_elem = stat.query_selector('.stat__value')

                    if label_elem and value_elem:
                        label = label_elem.inner_text().strip()
                        value = value_elem.inner_text().strip()
                        performance[label] = value
                except Exception as e:
                    continue

            return performance

        except Exception as e:
            print(f"Error scraping performance: {e}")
            return {}

    def scrape_all(self):
        """Scrape all stats and save to cache"""
        print("Starting scraper...")

        with sync_playwright() as p:
            try:
                # Launch browser
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

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
