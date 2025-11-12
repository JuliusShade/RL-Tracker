"""
Debug script to inspect RL Tracker website structure
"""
import yaml
from playwright.sync_api import sync_playwright
import time

# Load config
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

platform = config['profile']['platform']
username = config['profile']['username']

url = f"https://rocketleague.tracker.network/rocket-league/profile/{platform}/{username}/overview"

print(f"Opening: {url}")

with sync_playwright() as p:
    # Launch in headed mode with slow motion
    browser = p.chromium.launch(headless=False, slow_mo=1000)
    page = browser.new_page()

    # Navigate to the page
    page.goto(url, timeout=60000)
    print("Page loaded, waiting for content...")

    # Wait for page to settle
    try:
        page.wait_for_load_state('networkidle', timeout=30000)
    except Exception as e:
        print(f"Network idle timeout: {e}")

    # Take screenshot
    page.screenshot(path="debug_screenshot.png")
    print("Screenshot saved to debug_screenshot.png")

    # Save HTML
    html = page.content()
    with open('debug_page.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("HTML saved to debug_page.html")

    # Try to find playlists with different selectors
    print("\n=== Looking for playlist elements ===")

    selectors_to_try = [
        '.playlist',
        '[class*="playlist"]',
        '[class*="Playlist"]',
        '[data-testid*="playlist"]',
        '.stat-container',
        '[class*="stat"]',
        'div[class*="rank"]',
        '.ranked',
        '[class*="Ranked"]',
    ]

    for selector in selectors_to_try:
        try:
            elements = page.query_selector_all(selector)
            if elements:
                print(f"✓ Found {len(elements)} elements with selector: {selector}")
                if elements:
                    first = elements[0]
                    print(f"  First element HTML: {first.inner_html()[:200]}")
            else:
                print(f"✗ No elements found for: {selector}")
        except Exception as e:
            print(f"✗ Error with selector {selector}: {e}")

    print("\n=== Page structure analysis ===")
    # Look for main content divs
    main_selectors = ['main', '[role="main"]', '#main', '.main-content']
    for sel in main_selectors:
        try:
            elem = page.query_selector(sel)
            if elem:
                print(f"✓ Found main content with: {sel}")
        except:
            pass

    # Keep browser open for manual inspection
    print("\nBrowser will stay open for 60 seconds for manual inspection...")
    time.sleep(60)

    browser.close()
    print("Done!")
