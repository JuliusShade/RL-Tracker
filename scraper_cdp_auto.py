"""
Rocket League Tracker Scraper using Real Chrome Browser (Automated)
Uses Chrome DevTools Protocol (CDP) without manual prompts
"""

import json
import time
import yaml
import random
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


class ChromeCDPScraper:
    """Scraper that connects to real Chrome browser via CDP"""

    def __init__(self, config_path="config.yaml"):
        """Initialize scraper"""
        self.config = self._load_config(config_path)

        # Project root directories
        self.project_root = Path(__file__).parent
        self.html_dir = self.project_root / "data" / "html"
        self.html_dir.mkdir(parents=True, exist_ok=True)
        self.cache_path = self.project_root / self.config['cache']['path']

    def _load_config(self, config_path):
        """Load configuration from YAML"""
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

    def is_cloudflare_blocking(self, page):
        """Detect if Cloudflare is blocking"""
        try:
            html = page.content()
            indicators = [
                'Verify you are human',
                'Cloudflare',
                'Ray ID:',
                'Checking your browser',
                'Just a moment'
            ]
            matches = sum(1 for indicator in indicators if indicator in html)
            return matches >= 2
        except:
            return False

    def wait_for_cloudflare_clearance(self, page, max_wait=180):
        """Wait for Cloudflare clearance"""
        print("\n" + "="*60)
        print("CLOUDFLARE VERIFICATION NEEDED")
        print("="*60)
        print("\nPlease complete the Cloudflare verification in the Edge browser.")
        print("The scraper will continue automatically once cleared.")
        print(f"Waiting up to {max_wait} seconds...\n")

        start_time = time.time()
        while time.time() - start_time < max_wait:
            time.sleep(3)

            if not self.is_cloudflare_blocking(page):
                print("\n[SUCCESS] Cloudflare cleared!\n")
                return True

            elapsed = int(time.time() - start_time)
            if elapsed % 15 == 0:
                print(f"Still waiting... ({elapsed}s)")

        print("\n[TIMEOUT] Cloudflare not cleared\n")
        return False

    def inject_stealth_scripts(self, page):
        """Inject anti-detection JavaScript (minimal to avoid breaking Cloudflare)"""
        try:
            stealth_js = """
            // Override navigator.webdriver - the main automation indicator
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // Add chrome runtime object if it doesn't exist
            if (!window.chrome) {
                window.chrome = {
                    runtime: {}
                };
            }
            """
            page.evaluate(stealth_js)
            print("   [STEALTH] Injected minimal anti-detection scripts")
        except Exception as e:
            print(f"   [WARNING] Failed to inject stealth scripts: {e}")

    def scrape_page(self, page, url, page_name, skip_navigation=False):
        """Scrape a single page"""
        print(f"\n>> Scraping {page_name}...")

        try:
            if skip_navigation:
                # Using existing tab - just grab current HTML
                print("   [EXISTING TAB] Using already-loaded page")
                print(f"   Current URL: {page.url[:80]}...")

                # Quick check that page has content
                try:
                    page.wait_for_selector('text="Ranked"', timeout=2000)
                    print("   [SUCCESS] Page has stats loaded!")
                except:
                    print("   [WARNING] Page may not have stats loaded")

            else:
                # Navigate to page as normal
                print(f"   URL: {url[:80]}...")

                # Inject stealth scripts before navigation
                self.inject_stealth_scripts(page)

                # Random delay before navigation (appear more human)
                delay = random.uniform(1.0, 3.0)
                print(f"   Waiting {delay:.1f}s before navigation...")
                time.sleep(delay)

                # Navigate to page
                page.goto(url, wait_until="domcontentloaded", timeout=90000)
                print("   Page loaded (DOM ready)")

                # Re-inject stealth scripts after page load
                self.inject_stealth_scripts(page)

                # Check for Cloudflare first
                if self.is_cloudflare_blocking(page):
                    print(f"[CLOUDFLARE] Challenge detected on {page_name}")
                    if not self.wait_for_cloudflare_clearance(page):
                        print(f"   Failed to clear Cloudflare")
                        return False

                # Wait for JavaScript to render
                print("   Waiting for content to render...")
                time.sleep(5)

                # Try to wait for networkidle
                try:
                    page.wait_for_load_state("networkidle", timeout=30000)
                    print("   Page fully loaded (network idle)")
                except Exception as e:
                    print(f"   Note: networkidle timeout (continuing anyway)")

                # Wait for stats to be populated (client-side rendering)
                print("   Waiting for client-side rendering to complete...")

                # Try multiple selectors to detect when content is loaded
                content_loaded = False
                selectors_to_try = [
                    'text="Ranked Duel"',  # Playlist name
                    'text="Champion"',  # Rank tier
                    'text="Diamond"',  # Rank tier
                    'text="Lifetime"',  # Lifetime stats section
                    'span:has-text("MMR")',  # MMR text
                ]

                for selector in selectors_to_try:
                    try:
                        page.wait_for_selector(selector, timeout=10000)
                        print(f"   Stats loaded successfully! (found: {selector})")
                        content_loaded = True
                        break
                    except:
                        continue

                if not content_loaded:
                    print(f"   Warning: Stats elements not found after 50s wait")
                    # Take a screenshot for debugging
                    page.screenshot(path=str(self.project_root / "debug_no_stats.png"))
                    print(f"   Debug screenshot saved: debug_no_stats.png")

                # Additional wait to ensure all data is populated
                time.sleep(5)

                # Simulate human-like behavior
                self.simulate_human_behavior(page)

            # Save HTML
            html = page.content()

            if len(html) < 5000:
                print(f"[WARNING] HTML is very small ({len(html)} bytes) - may be blocked")

            html_file = self.html_dir / f"{page_name}.html"
            html_file.write_text(html, encoding="utf-8")

            print(f"[SUCCESS] Saved {page_name}.html ({len(html)/1024:.1f} KB)")

            # Take screenshot
            screenshot_path = self.project_root / f"{page_name}_screenshot.png"
            page.screenshot(path=str(screenshot_path))
            print(f"   Screenshot: {page_name}_screenshot.png")

            return True

        except PlaywrightTimeout as e:
            print(f"[TIMEOUT] {page_name}: {e}")
            return False

        except Exception as e:
            print(f"[ERROR] {page_name} failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def setup_stealth_page(self, page):
        """Configure page for stealth mode"""
        try:
            # Set realistic viewport
            page.set_viewport_size({"width": 1920, "height": 1080})

            # Set extra HTTP headers to appear more like a real browser
            page.set_extra_http_headers({
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1"
            })

            print("   [STEALTH] Configured page headers and viewport")
        except Exception as e:
            print(f"   [WARNING] Failed to setup stealth page: {e}")

    def simulate_human_behavior(self, page):
        """Simulate human-like interactions"""
        try:
            # Random mouse movements
            for _ in range(random.randint(2, 4)):
                x = random.randint(100, 1800)
                y = random.randint(100, 1000)
                page.mouse.move(x, y)
                time.sleep(random.uniform(0.1, 0.3))

            # Random scroll
            scroll_amount = random.randint(100, 500)
            page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            time.sleep(random.uniform(0.5, 1.0))

            # Scroll back up
            page.evaluate(f"window.scrollBy(0, -{scroll_amount})")
            time.sleep(random.uniform(0.3, 0.7))

            print("   [STEALTH] Simulated human behavior")
        except Exception as e:
            print(f"   [WARNING] Failed to simulate human behavior: {e}")

    def find_existing_tracker_page(self, context):
        """Find an existing tab with RL Tracker page open"""
        overview_url = self.config['urls']['overview']

        for page in context.pages:
            try:
                current_url = page.url
                # Check if this page is the RL Tracker overview page
                if 'rocketleague.tracker.network' in current_url and 'overview' in current_url:
                    print(f"[SUCCESS] Found existing RL Tracker tab!")
                    print(f"   URL: {current_url[:80]}...")
                    return page
            except:
                continue

        return None

    def scrape_all_pages(self):
        """Scrape using real Chrome browser"""
        print("\n" + "="*60)
        print("CHROME CDP SCRAPER (AUTOMATED)")
        print("="*60)
        print("\nConnecting to Edge browser on port 9222...")

        with sync_playwright() as p:
            try:
                # Connect to existing Chrome/Edge instance
                browser = p.chromium.connect_over_cdp("http://localhost:9222")
                print("[SUCCESS] Connected to Edge browser")

                context = browser.contexts[0]

                # First, check if RL Tracker page is already open
                existing_page = self.find_existing_tracker_page(context)

                if existing_page:
                    print("[USING EXISTING TAB] Grabbing HTML from already-open page")
                    page = existing_page
                else:
                    print("[NO EXISTING TAB] Will navigate to page")
                    page = context.pages[0] if context.pages else context.new_page()
                    # Configure page for stealth
                    self.setup_stealth_page(page)

                # Scrape only overview page (contains all needed data)
                pages_to_scrape = {
                    'overview': self.config['urls']['overview']
                }

                results = {}
                for page_name, url in pages_to_scrape.items():
                    # If using existing tab, skip navigation
                    skip_navigation = (existing_page is not None)
                    success = self.scrape_page(page, url, page_name, skip_navigation=skip_navigation)
                    results[page_name] = success
                    if success:
                        time.sleep(2)

                # Don't close browser
                browser.close()

                # Summary
                print("\n" + "="*60)
                print("SCRAPING SUMMARY")
                print("="*60)
                for page_name, success in results.items():
                    status = "[SUCCESS]" if success else "[FAILED]"
                    print(f"  {status} {page_name}")
                print("="*60 + "\n")

                return any(results.values())

            except Exception as e:
                print(f"\n[ERROR] Could not connect to Edge: {e}")
                print("\nMake sure Edge is running with:")
                print('& "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe" --remote-debugging-port=9222 --user-data-dir="C:\\temp\\edge_debug"')
                import traceback
                traceback.print_exc()
                return False

    def run_once(self):
        """Run scraper once"""
        success = self.scrape_all_pages()

        if success:
            print("\n>> Running parser...")
            try:
                from parser import parse_all
                parse_all()
                return True
            except Exception as e:
                print(f"[ERROR] Parser failed: {e}")
                import traceback
                traceback.print_exc()
                return False
        return False


def main():
    """Main entry point"""
    scraper = ChromeCDPScraper()
    scraper.run_once()


if __name__ == "__main__":
    main()
