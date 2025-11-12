"""
Enhanced Rocket League Tracker Scraper with Cloudflare Bypass
Uses multi-layered approach to bypass Cloudflare protection
"""

import json
import os
import yaml
import time
import random
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


class CloudflareBypass:
    """Handles Cloudflare detection and bypass strategies"""

    @staticmethod
    def is_cloudflare_challenge(page):
        """Detect if page is showing Cloudflare challenge"""
        try:
            page_text = page.inner_text('body')
            cloudflare_indicators = [
                'Verify you are human',
                'Cloudflare',
                'Ray ID',
                'Performance & security by Cloudflare',
                'Just a moment',
                'Checking your browser'
            ]

            # Count how many indicators are present
            matches = sum(1 for indicator in cloudflare_indicators if indicator in page_text)

            return matches >= 2  # If 2+ indicators, likely Cloudflare
        except:
            return False

    @staticmethod
    def get_user_agents():
        """Return list of realistic user agents"""
        return [
            # Chrome on Windows (recent versions)
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',

            # Firefox on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0',

            # Edge on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
        ]

    @staticmethod
    def get_random_viewport():
        """Return random realistic viewport size"""
        viewports = [
            {'width': 1920, 'height': 1080},
            {'width': 1366, 'height': 768},
            {'width': 1536, 'height': 864},
            {'width': 1440, 'height': 900},
            {'width': 2560, 'height': 1440},
        ]
        return random.choice(viewports)


class RLTrackerScraper:
    """Scrapes Rocket League stats from tracker.network with Cloudflare bypass"""

    def __init__(self, config_path="config.yaml"):
        """Initialize scraper with configuration"""
        self.config = self._load_config(config_path)
        cache_path_str = self.config['cache']['path']
        if cache_path_str.startswith('~'):
            self.cache_path = Path(cache_path_str).expanduser()
        else:
            self.cache_path = Path(__file__).parent / cache_path_str
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)

        # User data directory for persistent sessions
        self.user_data_dir = Path(__file__).parent / ".browser_data"
        self.user_data_dir.mkdir(exist_ok=True)

    def _load_config(self, config_path):
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        platform = config['profile']['platform']
        username = config['profile']['username']

        for key in config['urls']:
            config['urls'][key] = config['urls'][key].format(
                platform=platform,
                username=username
            )

        return config

    def _add_stealth_scripts(self, page):
        """Add scripts to hide automation and appear more human"""
        page.add_init_script("""
            // Overwrite the `webdriver` property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // Overwrite the `plugins` property to use a custom getter
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            // Overwrite the `languages` property
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });

            // Overwrite chrome property
            window.chrome = {
                runtime: {}
            };

            // Overwrite permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)

    def _wait_with_retry(self, page, selector, timeout=15000, max_retries=3):
        """Wait for selector with retry logic"""
        for attempt in range(max_retries):
            try:
                page.wait_for_selector(selector, timeout=timeout)
                return True
            except PlaywrightTimeout:
                if attempt < max_retries - 1:
                    print(f"Timeout waiting for {selector}, retrying ({attempt + 1}/{max_retries})...")
                    time.sleep(random.uniform(1, 3))
                else:
                    return False
        return False

    def _navigate_with_checks(self, page, url, wait_selector='h1, [class*="profile"]'):
        """Navigate to URL and check for Cloudflare"""
        print(f"Navigating to {url[:50]}...")

        # Navigate with extended timeout
        page.goto(url, timeout=60000, wait_until='domcontentloaded')

        # Initial wait
        time.sleep(random.uniform(2, 4))

        # Check for Cloudflare challenge
        if CloudflareBypass.is_cloudflare_challenge(page):
            print("[CLOUDFLARE] Challenge detected! Waiting for it to complete...")

            # Wait longer for Cloudflare to complete (up to 30 seconds)
            max_wait = 30
            start_time = time.time()

            while time.time() - start_time < max_wait:
                time.sleep(2)
                if not CloudflareBypass.is_cloudflare_challenge(page):
                    print("[CLOUDFLARE] Challenge passed!")
                    break
            else:
                print("[CLOUDFLARE] Challenge did not complete automatically")
                return False

        # Wait for main content
        if not self._wait_with_retry(page, wait_selector):
            print(f"Could not find selector: {wait_selector}")
            return False

        # Extra time for dynamic content
        time.sleep(random.uniform(2, 3))

        return True

    def scrape_with_strategy(self, strategy_name, headless=True, slow_mo=None):
        """Scrape with a specific strategy"""
        print(f"\n{'='*60}")
        print(f"Trying strategy: {strategy_name}")
        print(f"{'='*60}\n")

        with sync_playwright() as p:
            try:
                # Choose random user agent
                user_agent = random.choice(CloudflareBypass.get_user_agents())
                viewport = CloudflareBypass.get_random_viewport()

                print(f"User Agent: {user_agent[:80]}...")
                print(f"Viewport: {viewport}")
                print(f"Headless: {headless}")

                # Browser arguments for stealth
                args = [
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu'
                ]

                # Launch browser
                browser = p.chromium.launch(
                    headless=headless,
                    args=args,
                    slow_mo=slow_mo
                )

                # Context options
                context_options = {
                    'viewport': viewport,
                    'user_agent': user_agent,
                    'locale': 'en-US',
                    'timezone_id': 'America/New_York',
                    'permissions': ['geolocation'],
                    'color_scheme': 'dark',
                }

                # Use persistent context for session reuse in some strategies
                if 'persistent' in strategy_name.lower():
                    context = browser.new_context(
                        **context_options,
                        storage_state=str(self.user_data_dir / "state.json") if (self.user_data_dir / "state.json").exists() else None
                    )
                else:
                    context = browser.new_context(**context_options)

                page = context.new_page()

                # Add stealth scripts
                self._add_stealth_scripts(page)

                # Add extra headers
                context.set_extra_http_headers({
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Cache-Control': 'max-age=0',
                })

                # Scrape all pages
                print("\n>> Scraping overview...")
                overview = self.scrape_overview(page)

                # Random delay between requests
                time.sleep(random.uniform(3, 6))

                print("\n>> Scraping matches...")
                matches = self.scrape_matches(page)

                time.sleep(random.uniform(3, 6))

                print("\n>> Scraping performance...")
                performance = self.scrape_performance(page)

                # Save session state for reuse
                if 'persistent' in strategy_name.lower():
                    context.storage_state(path=str(self.user_data_dir / "state.json"))

                # Close browser
                browser.close()

                # Combine all data
                data = {
                    'timestamp': datetime.now().isoformat(),
                    'overview': overview,
                    'recent_matches': matches,
                    'performance': performance
                }

                # Check if we got meaningful data
                has_data = bool(overview or matches or performance)

                if has_data:
                    print(f"\n[SUCCESS] Strategy '{strategy_name}' successful!")
                    return data
                else:
                    print(f"\n[WARNING] Strategy '{strategy_name}' returned empty data")
                    return None

            except Exception as e:
                print(f"\n[ERROR] Strategy '{strategy_name}' failed: {e}")
                import traceback
                traceback.print_exc()
                return None

    def scrape_overview(self, page):
        """Scrape overview page for rank information"""
        try:
            if not self._navigate_with_checks(page, self.config['urls']['overview']):
                print("Failed to load overview page properly")
                page_text = page.inner_text('body')[:500]
                print(f"Page content: {page_text}")
                return {}

            # Take screenshot for debugging
            page.screenshot(path="scraper_debug.png")

            stats = {}

            # Try to find rank cards
            playlist_selectors = [
                '[class*="playlist"]',
                '[class*="rank-card"]',
                '[class*="mode"]',
                '[data-mode]',
                'div[class*="giant-stat"]',
            ]

            playlists = []
            for selector in playlist_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    if elements and len(elements) > 0:
                        playlists = elements
                        print(f"[+] Found {len(playlists)} playlist elements")
                        break
                except:
                    continue

            if not playlists:
                print("[x] No playlist elements found")
                return stats

            # Parse playlists (existing logic)
            for i, playlist in enumerate(playlists):
                try:
                    text = playlist.inner_text()
                    if len(text) < 3 or 'Login' in text or 'Sign' in text:
                        continue

                    lines = [line.strip() for line in text.split('\n') if line.strip()]

                    # Look for playlist names and ranks
                    for j, line in enumerate(lines):
                        if any(mode in line for mode in ['Duel', 'Doubles', 'Standard', '1v1', '2v2', '3v3']):
                            playlist_name = line

                            rank = "Unranked"
                            mmr = 0

                            # Find rank and MMR in nearby lines
                            for k in range(j, min(j + 5, len(lines))):
                                next_line = lines[k]
                                if any(rank_name in next_line for rank_name in ['Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond', 'Champion', 'Grand Champion', 'Supersonic Legend']):
                                    rank = next_line
                                elif next_line.replace(',', '').isdigit():
                                    mmr = int(next_line.replace(',', ''))

                            stats[playlist_name] = {
                                'rank': rank,
                                'mmr': mmr
                            }
                            break

                except Exception as e:
                    continue

            print(f"[+] Scraped {len(stats)} playlists")
            return stats

        except Exception as e:
            print(f"Error scraping overview: {e}")
            return {}

    def scrape_matches(self, page):
        """Scrape recent matches"""
        try:
            if not self._navigate_with_checks(page, self.config['urls']['matches']):
                print("Failed to load matches page properly")
                return []

            matches = []

            match_selectors = [
                '[class*="match"]',
                '[class*="game"]',
                '[class*="history"]',
                'tr', 'div[class*="row"]'
            ]

            match_elements = []
            for selector in match_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    if elements and len(elements) > 2:
                        match_elements = elements
                        print(f"[+] Found {len(match_elements)} match elements")
                        break
                except:
                    continue

            if not match_elements:
                print("[x] No match elements found")
                return matches

            # Parse matches (existing logic) - taking top 20
            for i, match in enumerate(match_elements[:20]):
                try:
                    text = match.inner_text()
                    if len(text) < 5:
                        continue

                    lines = [line.strip() for line in text.split('\n') if line.strip()]

                    result = "Unknown"
                    playlist = "Unknown"
                    mmr_change = "0"
                    date_str = None

                    for line in lines:
                        if any(w in line for w in ['Win', 'Victory', 'Loss', 'Defeat']):
                            result = line
                        elif any(mode in line for mode in ['Duel', 'Doubles', 'Standard', '1v1', '2v2', '3v3']):
                            playlist = line
                        elif line.startswith(('+', '-')) and any(c.isdigit() for c in line):
                            mmr_change = line.split()[0]
                        elif any(c.isdigit() for c in line):
                            if '/' in line or '-' in line or any(month in line.lower() for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
                                date_str = self._parse_date(line)
                            elif 'ago' in line.lower() or 'day' in line.lower() or 'hour' in line.lower():
                                date_str = self._parse_relative_date(line)

                    if result != "Unknown" or playlist != "Unknown":
                        match_data = {
                            'result': result,
                            'playlist': playlist,
                            'mmr_change': mmr_change
                        }
                        if date_str:
                            match_data['date'] = date_str
                        matches.append(match_data)

                except Exception as e:
                    continue

            print(f"[+] Scraped {len(matches)} matches")
            return matches

        except Exception as e:
            print(f"Error scraping matches: {e}")
            return []

    def scrape_performance(self, page):
        """Scrape performance metrics"""
        try:
            if not self._navigate_with_checks(page, self.config['urls']['performance']):
                print("Failed to load performance page properly")
                return {}

            performance = {}

            stat_selectors = [
                '[class*="stat"]',
                '[class*="metric"]',
                '[class*="performance"]',
                'div[class*="giant"]'
            ]

            stat_elements = []
            for selector in stat_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    if elements and len(elements) > 0:
                        stat_elements = elements
                        print(f"[+] Found {len(stat_elements)} stat elements")
                        break
                except:
                    continue

            if not stat_elements:
                print("[x] No stat elements found")
                return performance

            # Parse stats
            for i, stat in enumerate(stat_elements[:15]):
                try:
                    text = stat.inner_text()
                    lines = [line.strip() for line in text.split('\n') if line.strip()]

                    if len(lines) < 1:
                        continue

                    for j in range(len(lines) - 1):
                        label = lines[j]
                        value = lines[j + 1]

                        if any(skip in label.lower() for skip in ['login', 'sign', 'menu', 'nav', 'overview', 'matches', 'performance']):
                            continue

                        if len(label) > 1 and len(label) < 50:
                            value_clean = value.replace(',', '').replace('.', '').replace('%', '').replace(':', '')
                            if value_clean.replace('-', '').isdigit() or any(c.isdigit() for c in value):
                                if label not in performance:
                                    performance[label] = value

                except Exception as e:
                    continue

            print(f"[+] Scraped {len(performance)} performance stats")
            return performance

        except Exception as e:
            print(f"Error scraping performance: {e}")
            return {}

    def _parse_date(self, date_text):
        """Parse date from text"""
        try:
            date_text = date_text.strip()
            formats = ['%m/%d/%Y', '%Y-%m-%d', '%d/%m/%Y', '%b %d, %Y', '%B %d, %Y', '%m-%d-%Y']

            for fmt in formats:
                try:
                    dt = datetime.strptime(date_text, fmt)
                    return dt.strftime('%Y-%m-%d')
                except:
                    continue
            return None
        except:
            return None

    def _parse_relative_date(self, relative_text):
        """Parse relative date like '2 days ago'"""
        try:
            from datetime import timedelta
            import re

            text = relative_text.lower()
            today = datetime.now()

            match = re.search(r'(\d+)', text)
            if not match:
                return today.strftime('%Y-%m-%d')

            num = int(match.group(1))

            if 'hour' in text or 'hr' in text:
                return today.strftime('%Y-%m-%d')
            elif 'day' in text:
                dt = today - timedelta(days=num)
                return dt.strftime('%Y-%m-%d')
            elif 'week' in text:
                dt = today - timedelta(weeks=num)
                return dt.strftime('%Y-%m-%d')
            elif 'month' in text:
                dt = today - timedelta(days=num*30)
                return dt.strftime('%Y-%m-%d')

            return today.strftime('%Y-%m-%d')
        except:
            return None

    def scrape_all(self):
        """Scrape with multiple fallback strategies"""
        print("\n" + "="*60)
        print("ENHANCED ROCKET LEAGUE TRACKER SCRAPER")
        print("="*60 + "\n")

        strategies = [
            ("Enhanced Stealth (Headless)", True, None),
            ("Slow Stealth (Headless)", True, 100),
            ("Visible Browser", False, None),
            ("Visible Browser (Slow)", False, 100),
            ("Persistent Session (Visible)", False, None),
        ]

        for strategy_name, headless, slow_mo in strategies:
            data = self.scrape_with_strategy(strategy_name, headless, slow_mo)

            if data and (data['overview'] or data['recent_matches'] or data['performance']):
                # Success! Save data
                with open(self.cache_path, 'w') as f:
                    json.dump(data, f, indent=2)

                print(f"\n{'='*60}")
                print(f"[SUCCESS] Data saved to {self.cache_path}")
                print(f"{'='*60}\n")
                return data
            else:
                print(f"\n[WARNING] Strategy '{strategy_name}' did not return usable data, trying next...")
                time.sleep(5)  # Wait before next strategy

        print("\n" + "="*60)
        print("[FAILED] ALL STRATEGIES FAILED")
        print("="*60)
        print("\nTroubleshooting tips:")
        print("1. Check your internet connection")
        print("2. Verify your username and platform in config.yaml")
        print("3. Try running again later (Cloudflare may have rate-limited you)")
        print("4. Check if tracker.network is accessible in your browser")
        print("="*60 + "\n")
        return None


def main():
    """Main entry point"""
    scraper = RLTrackerScraper()
    data = scraper.scrape_all()

    if data:
        print("\n>> Scraped Data Summary:")
        print(f"   Playlists: {len(data.get('overview', {}))}")
        print(f"   Matches: {len(data.get('recent_matches', []))}")
        print(f"   Performance Stats: {len(data.get('performance', {}))}")
    else:
        print("\n[FAILED] Scraping failed. Please check the errors above.")


if __name__ == "__main__":
    main()
