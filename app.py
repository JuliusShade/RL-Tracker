"""
Rocket League Stats Display App
PySide6 GUI that displays stats from cached data
"""

import json
import sys
import yaml
import subprocess
from datetime import datetime
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QScrollArea, QPushButton, QGridLayout, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QRect, QPoint, QThread, Signal
from PySide6.QtGui import QPixmap, QFont, QPalette, QColor, QPainter, QPen, QBrush
from rank_map import rank_icon_path
from activity_map import parse_activity_data, build_heatmap_widget


class RefreshWorker(QThread):
    """Background worker thread for scraping and parsing"""
    finished = Signal(bool, str)  # success, message

    def check_browser_running(self):
        """Check if browser is running with remote debugging"""
        import socket
        import urllib.request

        # Check if port 9222 is open
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('localhost', 9222))
            sock.close()

            if result == 0:
                # Port is open, verify it's actually a browser debugging interface
                try:
                    response = urllib.request.urlopen('http://localhost:9222/json/version', timeout=2)
                    if response.status == 200:
                        print("[Refresh] ✓ Browser detected on port 9222")
                        return True
                except:
                    print("[Refresh] Port 9222 open but not responding to browser API")
                    pass

            print("[Refresh] No browser detected on port 9222")
            return False
        except Exception as e:
            print(f"[Refresh] Browser check failed: {e}")
            return False

    def kill_existing_browser(self, browser_name):
        """Kill existing browser processes to free up debugging port"""
        try:
            if browser_name == "Edge":
                subprocess.run(["taskkill", "/F", "/IM", "msedge.exe"],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL,
                             timeout=5)
                print("[Refresh] Killed existing Edge processes")
            elif browser_name == "Chrome":
                subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL,
                             timeout=5)
                print("[Refresh] Killed existing Chrome processes")
            time.sleep(1)  # Wait for processes to fully terminate
        except Exception as e:
            print(f"[Refresh] Note: Could not kill existing processes (may not be running)")

    def start_browser(self):
        """Start Edge/Chrome with remote debugging (using normal profile for stealth)"""
        import platform
        import os

        print("[Refresh] Checking for browser with remote debugging...")
        print()
        print("[Refresh] ═══════════════════════════════════════════════")
        print("[Refresh] IMPORTANT: To use your existing browser tab:")
        print("[Refresh] 1. Close ALL Edge windows first")
        print("[Refresh] 2. Open PowerShell and run:")
        print('[Refresh]    Start-Process "msedge.exe" -ArgumentList "--remote-debugging-port=9222"')
        print("[Refresh] 3. In that Edge window, navigate to your RL Tracker profile")
        print("[Refresh] 4. Keep that tab open and click Refresh in this app")
        print("[Refresh] ═══════════════════════════════════════════════")
        print()

        # Try Edge first (more common on Windows)
        edge_paths = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ]

        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]

        browser_cmd = None
        browser_name = None

        # Find Edge
        for path in edge_paths:
            if Path(path).exists():
                browser_name = "Edge"
                # Minimal flags - just debugging port, nothing else
                # This makes it as close to normal browsing as possible
                browser_cmd = [
                    path,
                    "--remote-debugging-port=9222",
                ]
                print(f"[Refresh] Found Edge at: {path}")
                break

        # Try Chrome if Edge not found
        if not browser_cmd:
            for path in chrome_paths:
                if Path(path).exists():
                    browser_name = "Chrome"
                    browser_cmd = [
                        path,
                        "--remote-debugging-port=9222",
                    ]
                    print(f"[Refresh] Found Chrome at: {path}")
                    break

        if not browser_cmd:
            raise Exception("Could not find Edge or Chrome browser")

        # DON'T kill existing processes - reuse if possible
        # Check if browser already running
        if self.check_browser_running():
            print("[Refresh] Browser already running with debugging port - reusing!")
            return True

        print("[Refresh] No existing browser found, starting new instance...")
        print("[Refresh] Using default profile (cookies, history, extensions intact)")

        # Start browser in background
        subprocess.Popen(
            browser_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

        print("[Refresh] Browser started, waiting for it to be ready...")

        # Wait for browser to start (max 15 seconds)
        import time
        for i in range(30):
            time.sleep(0.5)
            if self.check_browser_running():
                print("[Refresh] Browser is ready!")
                time.sleep(2)  # Extra time for profile to fully load
                return True

        raise Exception("Browser started but debugging port not available")

    def run(self):
        """Run scraper and parser in background"""
        try:
            # Get the directory where the app is running
            import os
            import time
            project_dir = Path(__file__).parent

            # Step 1: Check if browser is running, start if needed
            print("[Refresh] Step 1: Checking browser...")
            if not self.check_browser_running():
                print("[Refresh] Browser not running with debugging port")
                try:
                    self.start_browser()
                except Exception as e:
                    error_msg = f"Failed to start browser: {str(e)}"
                    print(f"[Refresh] ERROR: {error_msg}")
                    self.finished.emit(False, error_msg)
                    return
            else:
                print("[Refresh] Browser already running with debugging port")

            # Check file timestamps BEFORE scraping
            print("\n[Refresh] Step 2: Checking file timestamps...")
            html_file = project_dir / "data" / "html" / "overview.html"
            json_file = project_dir / "rl_stats.json"

            html_mtime_before = html_file.stat().st_mtime if html_file.exists() else 0
            json_mtime_before = json_file.stat().st_mtime if json_file.exists() else 0

            print(f"[Refresh] File timestamps BEFORE scraping:")
            if html_file.exists():
                print(f"  - overview.html: {datetime.fromtimestamp(html_mtime_before)}")
            else:
                print(f"  - overview.html: NOT FOUND")
            if json_file.exists():
                print(f"  - rl_stats.json: {datetime.fromtimestamp(json_mtime_before)}")
            else:
                print(f"  - rl_stats.json: NOT FOUND")

            # Step 3: Run scraper to download HTML
            print(f"\n[Refresh] Step 3: Running scraper...")
            print(f"[Refresh] Scraper path: {project_dir / 'scraper_cdp_auto.py'}")

            result = subprocess.run(
                [sys.executable, str(project_dir / "scraper_cdp_auto.py")],
                capture_output=True,
                text=True,
                cwd=str(project_dir),  # Set working directory
                timeout=180  # 3 minute timeout
            )

            # Print output for debugging
            if result.stdout:
                print("\n[Refresh] Scraper output:")
                print(result.stdout)

            if result.stderr:
                print("\n[Refresh] Scraper errors:")
                print(result.stderr)

            if result.returncode != 0:
                error_msg = f"Scraper failed (exit code {result.returncode})"
                if result.stderr:
                    error_msg += f": {result.stderr[:500]}"
                print(f"[Refresh] {error_msg}")
                self.finished.emit(False, error_msg)
                return

            print("[Refresh] Scraper exit code: 0 (success)")

            # Wait a moment for files to be written
            time.sleep(0.5)

            # Step 4: Verify files were updated
            print(f"\n[Refresh] Step 4: Verifying files were updated...")

            html_mtime_after = html_file.stat().st_mtime if html_file.exists() else 0
            json_mtime_after = json_file.stat().st_mtime if json_file.exists() else 0

            print(f"[Refresh] File timestamps AFTER scraping:")
            if html_file.exists():
                print(f"  - overview.html: {datetime.fromtimestamp(html_mtime_after)}")
            else:
                print(f"  - overview.html: NOT FOUND")
            if json_file.exists():
                print(f"  - rl_stats.json: {datetime.fromtimestamp(json_mtime_after)}")
            else:
                print(f"  - rl_stats.json: NOT FOUND")

            # Verify files were actually updated
            html_updated = html_mtime_after > html_mtime_before
            json_updated = json_mtime_after > json_mtime_before

            print(f"\n[Refresh] Files updated?")
            print(f"  - overview.html: {'YES' if html_updated else 'NO'}")
            print(f"  - rl_stats.json: {'YES' if json_updated else 'NO'}")

            if not (html_updated or json_updated):
                error_msg = "Files were not updated! Check if Edge is running with --remote-debugging-port=9222"
                print(f"[Refresh] ERROR: {error_msg}")
                self.finished.emit(False, error_msg)
                return

            # Success!
            self.finished.emit(True, "Stats updated successfully!")

        except subprocess.TimeoutExpired:
            print("[Refresh] ERROR: Scraper timeout (3 min)")
            self.finished.emit(False, "Scraper timeout (3 min)")
        except Exception as e:
            import traceback
            print(f"[Refresh] ERROR: {str(e)}")
            traceback.print_exc()
            self.finished.emit(False, f"Error: {str(e)}")


class PieChartWidget(QWidget):
    """Custom pie chart widget for displaying goals/assists/saves distribution"""

    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data  # Dict with labels and values, e.g., {"Goals": 73, "Assists": 37, "Saves": 868}
        self.colors = {
            'Goals': QColor(255, 159, 64),      # Orange
            'Assists': QColor(54, 162, 235),     # Blue
            'Saves': QColor(75, 192, 192)        # Teal
        }
        self.setMinimumSize(150, 100)  # Reduced minimum size to fit better

    def paintEvent(self, event):
        """Draw the pie chart"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Calculate total
        total = sum(self.data.values())
        if total == 0:
            # Draw empty state
            painter.setPen(QPen(QColor(150, 150, 150)))
            painter.setFont(QFont("Arial", 10))
            painter.drawText(self.rect(), Qt.AlignCenter, "No data")
            return

        # Define pie chart rectangle (compact layout)
        width = self.width()
        height = self.height()

        # Reserve space for legend (100px on right side - more compact)
        legend_width = 100
        margin = 8

        # Calculate pie size to fit in available space
        available_width = max(20, width - legend_width - margin * 2)
        available_height = max(20, height - margin * 2)

        # Use smaller dimension, but cap at reasonable size
        pie_size = min(available_width, available_height, 80)  # Max 80px diameter

        # Position pie on left with small margin
        pie_x = margin
        pie_y = max(margin, (height - pie_size) // 2)
        pie_rect = QRect(pie_x, pie_y, pie_size, pie_size)

        # Draw pie slices
        start_angle = 0
        for label, value in self.data.items():
            angle = int((value / total) * 360 * 16)  # Qt uses 1/16th degree units

            # Set color
            color = self.colors.get(label, QColor(200, 200, 200))
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor(40, 40, 40), 2))

            # Draw slice
            painter.drawPie(pie_rect, start_angle, angle)
            start_angle += angle

        # Draw legend on the right (compact)
        legend_x = pie_x + pie_size + 10
        legend_item_height = 18  # Compact spacing
        legend_y = max(5, (height - len(self.data) * legend_item_height) // 2)
        painter.setFont(QFont("Arial", 7))  # Smaller font

        for i, (label, value) in enumerate(self.data.items()):
            y_pos = legend_y + i * legend_item_height

            # Draw color box (smaller)
            color = self.colors.get(label, QColor(200, 200, 200))
            painter.fillRect(legend_x, y_pos, 10, 10, color)
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.drawRect(legend_x, y_pos, 10, 10)

            # Draw label and value (compact)
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.drawText(legend_x + 14, y_pos + 8, f"{label}: {value}")


class RLStatsApp(QMainWindow):
    """Main application window for RL Stats Display"""

    def __init__(self):
        super().__init__()
        self.config = self._load_config()
        # Use project root for cache path
        cache_path_str = self.config['cache']['path']
        if cache_path_str.startswith('~'):
            self.cache_path = Path(cache_path_str).expanduser()
        else:
            # Relative to project root (same directory as app.py)
            self.cache_path = Path(__file__).parent / cache_path_str

        self.init_ui()
        self.load_stats()

        # Set up auto-refresh timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_stats)
        refresh_ms = self.config['refresh']['interval_minutes'] * 60 * 1000
        self.timer.start(refresh_ms)

    def _load_config(self):
        """Load configuration from YAML"""
        with open('config.yaml', 'r') as f:
            return yaml.safe_load(f)

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("RL Stats")

        # Set window size from config - optimize for Pi 7" display
        width = self.config['display']['window_width']
        height = self.config['display']['window_height']
        self.setGeometry(100, 100, width, height)

        # For Pi display, use fixed size to prevent resizing
        if width == 800 and height == 480:
            self.setFixedSize(width, height)

        # Apply theme
        self.apply_theme()

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(8)  # Reduced spacing for compact layout
        main_layout.setContentsMargins(10, 8, 10, 8)  # Reduced margins

        # Header - compact
        header = QLabel("RL Stats Dashboard")
        header.setFont(QFont("Arial", 16, QFont.Bold))  # Smaller font
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)

        # Player info and update time in one row
        info_layout = QHBoxLayout()
        info_layout.setSpacing(10)

        self.player_label = QLabel()
        self.player_label.setFont(QFont("Arial", 10))
        info_layout.addWidget(self.player_label)

        info_layout.addStretch()

        self.updated_label = QLabel("Last updated: Never")
        self.updated_label.setFont(QFont("Arial", 9))
        self.updated_label.setStyleSheet("color: #999999;")
        info_layout.addWidget(self.updated_label)

        main_layout.addLayout(info_layout)

        # Stats container - NO SCROLL AREA for Pi display
        stats_widget = QWidget()
        self.stats_layout = QVBoxLayout(stats_widget)
        self.stats_layout.setSpacing(8)
        self.stats_layout.setContentsMargins(0, 0, 0, 0)

        main_layout.addWidget(stats_widget)

        # Status label for refresh feedback
        self.status_label = QLabel("")
        self.status_label.setFont(QFont("Arial", 9))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #00d9ff; padding: 5px;")
        self.status_label.setMinimumHeight(20)
        main_layout.addWidget(self.status_label)

        # Refresh button - compact (store as instance variable)
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.refresh_btn.setMaximumWidth(120)
        self.refresh_btn.setMinimumHeight(30)
        self.refresh_btn.setFont(QFont("Arial", 10))

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        # Worker thread for background refresh
        self.refresh_worker = None

    def apply_theme(self):
        """Apply color theme to the application"""
        if self.config['display']['theme'] == 'dark':
            # Set application palette for dark theme
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor(26, 26, 26))
            palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
            palette.setColor(QPalette.Base, QColor(45, 45, 45))
            palette.setColor(QPalette.AlternateBase, QColor(35, 35, 35))
            palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
            palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
            palette.setColor(QPalette.Text, QColor(255, 255, 255))
            palette.setColor(QPalette.Button, QColor(45, 45, 45))
            palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
            palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
            self.setPalette(palette)

            self.setStyleSheet("""
                QMainWindow {
                    background-color: #1a1a1a;
                }
                QPushButton {
                    background-color: #0078d4;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 10px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #106ebe;
                }
                QFrame {
                    background-color: #2d2d2d;
                    border-radius: 10px;
                }
                QLabel {
                    color: #ffffff;
                    background: transparent;
                }
                QFrame QLabel {
                    color: #ffffff;
                    background: transparent;
                }
            """)
        else:
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #f0f0f0;
                    color: #000000;
                }
                QPushButton {
                    background-color: #0078d4;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 10px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #106ebe;
                }
                QFrame {
                    background-color: #ffffff;
                    border: 1px solid #cccccc;
                    border-radius: 10px;
                }
                QLabel {
                    color: #000000;
                    background: transparent;
                }
                QFrame QLabel {
                    color: #000000;
                    background: transparent;
                }
            """)

    def load_stats(self):
        """Load stats from cache file"""
        if not self.cache_path.exists():
            self.show_no_data_message()
            return

        try:
            with open(self.cache_path, 'r') as f:
                data = json.load(f)

            self.display_stats(data)

        except Exception as e:
            self.show_error_message(str(e))

    def refresh_data(self):
        """Trigger full refresh workflow (scrape + parse + reload)"""
        # Check if already refreshing
        if self.refresh_worker and self.refresh_worker.isRunning():
            print("[Refresh] Already refreshing...")
            self.status_label.setText("Already refreshing...")
            return

        # Disable button and show loading state
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("Refreshing...")
        self.status_label.setText("Downloading HTML from RL Tracker...")
        self.status_label.setStyleSheet("color: #00d9ff; padding: 5px;")
        print("[Refresh] Starting refresh workflow...")

        # Create and start worker thread
        self.refresh_worker = RefreshWorker()
        self.refresh_worker.finished.connect(self.on_refresh_complete)
        self.refresh_worker.start()

    def on_refresh_complete(self, success, message):
        """Handle refresh completion"""
        # Re-enable button
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("Refresh")

        if success:
            print(f"[Refresh] {message}")
            self.status_label.setText(f"✓ {message}")
            self.status_label.setStyleSheet("color: #4CAF50; padding: 5px;")  # Green
            # Reload stats from updated cache
            self.load_stats()

            # Clear status after 3 seconds
            QTimer.singleShot(3000, lambda: self.status_label.setText(""))
        else:
            print(f"[Refresh] Failed: {message}")
            self.status_label.setText(f"✗ {message}")
            self.status_label.setStyleSheet("color: #ff6b6b; padding: 5px;")  # Red

    def show_no_data_message(self):
        """Display message when no data is available"""
        # Clear existing stats
        self.clear_stats_layout()

        msg = QLabel("No stats available. Please run scraper.py first.")
        msg.setFont(QFont("Arial", 14))
        msg.setAlignment(Qt.AlignCenter)
        msg.setStyleSheet("color: #ff6b6b; padding: 50px;")
        self.stats_layout.addWidget(msg)

    def show_error_message(self, error):
        """Display error message"""
        self.clear_stats_layout()

        msg = QLabel(f"Error loading stats: {error}")
        msg.setFont(QFont("Arial", 12))
        msg.setAlignment(Qt.AlignCenter)
        msg.setStyleSheet("color: #ff6b6b; padding: 50px;")
        self.stats_layout.addWidget(msg)

    def clear_stats_layout(self):
        """Clear all widgets and layouts from stats layout"""
        while self.stats_layout.count():
            child = self.stats_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                # Recursively clear nested layouts
                self._clear_layout(child.layout())

    def _clear_layout(self, layout):
        """Recursively clear a layout"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self._clear_layout(child.layout())

    def display_stats(self, data):
        """Display stats in the UI"""
        # Clear existing stats
        self.clear_stats_layout()

        # Update player info
        platform = self.config['profile']['platform']
        username = self.config['profile']['username']
        self.player_label.setText(f"{username} ({platform.upper()})")

        # Update timestamp
        timestamp = data.get('timestamp', '')
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                formatted_time = dt.strftime("%m/%d %H:%M")
                self.updated_label.setText(f"Updated: {formatted_time}")
            except:
                self.updated_label.setText(f"Updated: {timestamp}")

        # Create horizontal layout for ranks and activity - wrap in container
        top_row_container = QWidget()
        top_row_container.setMinimumHeight(150)
        top_row_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        top_row = QHBoxLayout(top_row_container)
        top_row.setSpacing(10)
        top_row.setContentsMargins(0, 0, 0, 0)

        # Display rank information
        overview = data.get('overview', {})
        if overview:
            ranks_frame = self.create_ranks_section(overview)
            top_row.addWidget(ranks_frame, stretch=3)

        # Display activity heatmap
        # Support new format (activity_heatmap) or old format (recent_matches)
        heatmap_data = data.get('activity_heatmap', [])
        if heatmap_data:
            # New format: direct heatmap data
            activity_data = {item['date']: item['count'] for item in heatmap_data}
            heatmap_widget = build_heatmap_widget(activity_data, days=30)
            heatmap_widget.setMinimumHeight(150)
            heatmap_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
            top_row.addWidget(heatmap_widget, stretch=2)
        else:
            # Fallback to old format
            matches = data.get('recent_matches', [])
            if matches:
                activity_data = parse_activity_data(matches)
                heatmap_widget = build_heatmap_widget(activity_data, days=30)
                heatmap_widget.setMinimumHeight(150)
                heatmap_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
                top_row.addWidget(heatmap_widget, stretch=2)

        self.stats_layout.addWidget(top_row_container)

        # Display recent matches/sessions and pie chart side by side
        sessions = data.get('sessions', [])
        if sessions:
            # Create horizontal container for sessions and pie chart
            bottom_row_container = QWidget()
            bottom_row = QHBoxLayout(bottom_row_container)
            bottom_row.setSpacing(10)
            bottom_row.setContentsMargins(0, 0, 0, 0)

            # Left side: Recent sessions (half width)
            matches_frame = self.create_sessions_section(sessions)
            bottom_row.addWidget(matches_frame, stretch=1)

            # Right side: Pie chart (half width)
            pie_chart_frame = self.create_pie_chart_section(sessions)
            bottom_row.addWidget(pie_chart_frame, stretch=1)

            self.stats_layout.addWidget(bottom_row_container)
        else:
            # Fallback to old format
            matches = data.get('recent_matches', [])
            if matches:
                matches_frame = self.create_matches_section(matches)
                self.stats_layout.addWidget(matches_frame)

        # Display lifetime stats from overview data
        overview = data.get('overview', {})
        lifetime_stats = overview.get('__lifetime__', {})
        if lifetime_stats:
            lifetime_frame = self.create_lifetime_stats_section(lifetime_stats)
            self.stats_layout.addWidget(lifetime_frame)

        # No stretch at the end for compact layout

    def create_ranks_section(self, overview):
        """Create the ranks display section - scrollable"""
        # Main container
        container = QFrame()
        container.setMinimumHeight(150)
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(0)
        container_layout.setContentsMargins(8, 6, 8, 6)

        # Section title
        title = QLabel("Ranks")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        title.setStyleSheet("color: #ffffff !important; background-color: transparent;")
        title.setMinimumHeight(18)
        container_layout.addWidget(title)

        # Scrollable area for ranks
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: #1e1e1e;
                width: 8px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #555555;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #777777;
            }
        """)

        # Content widget inside scroll area
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 2, 0, 2)

        # Vertical list for playlists
        for playlist_name, stats in overview.items():
            # Skip lifetime stats (not a playlist)
            if playlist_name == '__lifetime__':
                continue

            # Create playlist widget
            playlist_widget = QWidget()
            playlist_widget.setMinimumHeight(36)  # Ensure container is tall enough for content
            playlist_layout = QHBoxLayout(playlist_widget)
            playlist_layout.setSpacing(8)
            playlist_layout.setContentsMargins(0, 2, 0, 2)

            # Rank icon - smaller
            rank_text = stats.get('rank', 'Unranked')
            icon_file = rank_icon_path(rank_text)

            rank_icon = QLabel()
            if icon_file and icon_file.exists():
                pixmap = QPixmap(str(icon_file))
                # Scale to appropriate size
                scaled_pixmap = pixmap.scaledToHeight(32, Qt.SmoothTransformation)
                rank_icon.setPixmap(scaled_pixmap)
                rank_icon.setFixedSize(32, 32)
            else:
                # Placeholder for unranked or missing icon
                rank_icon.setText("🏆")
                rank_icon.setFont(QFont("Arial", 16))
                rank_icon.setAlignment(Qt.AlignCenter)
                rank_icon.setFixedSize(32, 32)
                rank_icon.setStyleSheet("color: #999999 !important; background-color: transparent;")

            playlist_layout.addWidget(rank_icon)

            # Text info - horizontal for space efficiency
            # Playlist name
            name_label = QLabel(playlist_name)
            name_label.setFont(QFont("Arial", 9, QFont.Bold))
            name_label.setStyleSheet("color: #ffffff !important; background-color: transparent;")
            name_label.setMinimumWidth(80)
            name_label.setMaximumWidth(100)
            name_label.setWordWrap(True)
            name_label.setMinimumHeight(20)
            playlist_layout.addWidget(name_label)

            # Rank
            rank_label = QLabel(rank_text)
            rank_label.setFont(QFont("Arial", 9))
            rank_label.setStyleSheet("color: #4ecdc4 !important; background-color: transparent;")
            rank_label.setMinimumWidth(120)
            rank_label.setWordWrap(True)
            rank_label.setMinimumHeight(20)
            playlist_layout.addWidget(rank_label)

            # MMR
            mmr = stats.get('mmr', 0)
            mmr_label = QLabel(f"{int(mmr)} MMR")
            mmr_label.setFont(QFont("Arial", 9))
            mmr_label.setStyleSheet("color: #ffffff !important; background-color: transparent;")
            mmr_label.setAlignment(Qt.AlignRight)
            mmr_label.setMinimumHeight(20)
            mmr_label.setMinimumWidth(60)
            playlist_layout.addWidget(mmr_label)

            playlist_layout.addStretch()
            layout.addWidget(playlist_widget)

        # Add stretch at the end
        layout.addStretch()

        # Set scroll content
        scroll_area.setWidget(scroll_content)
        container_layout.addWidget(scroll_area)

        return container

    def create_sessions_section(self, sessions):
        """Create the recent sessions section - scrollable"""
        # Main container
        container = QFrame()
        container.setMinimumHeight(90)
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(0)
        container_layout.setContentsMargins(8, 6, 8, 6)

        # Section title
        title = QLabel("Recent Sessions")
        title.setFont(QFont("Arial", 11, QFont.Bold))
        title.setStyleSheet("color: #ffffff !important; background-color: transparent;")
        title.setMinimumHeight(18)
        container_layout.addWidget(title)

        # Scrollable area for sessions
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: #1e1e1e;
                width: 8px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #555555;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #777777;
            }
        """)

        # Content widget inside scroll area
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setSpacing(3)
        layout.setContentsMargins(0, 2, 0, 2)

        # Session list - show ALL sessions (scrollable)
        for i, session in enumerate(sessions, 1):
            session_widget = QWidget()
            session_widget.setMinimumHeight(40)  # Increased to prevent text cropping
            session_layout = QVBoxLayout(session_widget)
            session_layout.setContentsMargins(0, 2, 0, 2)
            session_layout.setSpacing(2)

            # Session header (time ago + wins)
            header_widget = QWidget()
            header_layout = QHBoxLayout(header_widget)
            header_layout.setContentsMargins(0, 0, 0, 0)
            header_layout.setSpacing(6)

            # Time ago
            time_label = QLabel(session.get('time_ago', 'Unknown'))
            time_label.setFont(QFont("Arial", 9, QFont.Bold))
            time_label.setStyleSheet("color: #00d9ff !important; background-color: transparent;")
            time_label.setMinimumHeight(18)
            time_label.setWordWrap(True)
            header_layout.addWidget(time_label)

            # Wins
            wins = session.get('wins', 0)
            if wins > 0:
                wins_label = QLabel(f"{wins}W")
                wins_label.setFont(QFont("Arial", 8))
                wins_label.setStyleSheet("color: #4CAF50 !important; background-color: transparent;")
                wins_label.setMinimumHeight(18)
                header_layout.addWidget(wins_label)

            # Stats (goals/assists if available)
            if 'goals' in session and 'assists' in session:
                stats_label = QLabel(f"{session['goals']}G {session['assists']}A")
                stats_label.setFont(QFont("Arial", 8))
                stats_label.setStyleSheet("color: #999999 !important; background-color: transparent;")
                stats_label.setMinimumHeight(18)
                header_layout.addWidget(stats_label)

            header_layout.addStretch()
            session_layout.addWidget(header_widget)

            # Matches in session
            matches = session.get('matches', [])
            if matches:
                matches_text = ", ".join([
                    f"{m['count']}x {m['playlist'].replace('Ranked ', '')}"
                    for m in matches[:2]  # Show max 2 playlists per session
                ])
                matches_label = QLabel(matches_text)
                matches_label.setFont(QFont("Arial", 8))
                matches_label.setStyleSheet("color: #cccccc !important; background-color: transparent;")
                matches_label.setMinimumHeight(18)
                matches_label.setWordWrap(True)
                session_layout.addWidget(matches_label)

            layout.addWidget(session_widget)

        # Add stretch at the end
        layout.addStretch()

        # Set scroll content
        scroll_area.setWidget(scroll_content)
        container_layout.addWidget(scroll_area)

        return container

    def create_matches_section(self, matches):
        """Create the recent matches section - compact"""
        frame = QFrame()
        frame.setMinimumHeight(90)  # Ensure frame is tall enough for title + 3 matches
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout = QVBoxLayout(frame)
        layout.setSpacing(3)
        layout.setContentsMargins(8, 6, 8, 6)

        # Section title
        title = QLabel("Recent Matches")
        title.setFont(QFont("Arial", 11, QFont.Bold))
        title.setStyleSheet("color: #ffffff !important; background-color: transparent;")
        title.setMinimumHeight(18)
        layout.addWidget(title)

        # Match list - show only top 3 for compact layout
        for i, match in enumerate(matches[:3], 1):
            match_widget = QWidget()
            match_widget.setMinimumHeight(20)  # Ensure container is tall enough for content
            match_layout = QHBoxLayout(match_widget)
            match_layout.setContentsMargins(0, 1, 0, 1)
            match_layout.setSpacing(6)

            # Result indicator (W/L)
            result = match.get('result', 'Unknown')
            result_short = "W" if 'Win' in result or 'Victory' in result else "L" if 'Loss' in result or 'Defeat' in result else "?"
            result_label = QLabel(result_short)
            result_label.setFont(QFont("Arial", 10, QFont.Bold))
            result_label.setFixedWidth(15)
            result_label.setMinimumHeight(16)

            if result_short == "W":
                result_label.setStyleSheet("color: #51cf66;")
            elif result_short == "L":
                result_label.setStyleSheet("color: #ff6b6b;")

            match_layout.addWidget(result_label)

            # Playlist - shortened
            playlist = match.get('playlist', 'Unknown')
            playlist_short = playlist.replace('Ranked Doubles', '2v2').replace('Ranked Duel', '1v1').replace('Ranked Standard', '3v3')
            playlist_label = QLabel(playlist_short[:10])
            playlist_label.setFont(QFont("Arial", 10))
            playlist_label.setStyleSheet("color: #ffffff !important; background-color: transparent;")
            playlist_label.setFixedWidth(70)
            playlist_label.setMinimumHeight(16)
            match_layout.addWidget(playlist_label)

            match_layout.addStretch()

            # MMR change
            mmr_change = match.get('mmr_change', '0')
            mmr_label = QLabel(mmr_change)
            mmr_label.setFont(QFont("Arial", 10, QFont.Bold))
            mmr_label.setMinimumHeight(16)
            if '+' in mmr_change or (mmr_change.replace('.', '').replace('-', '').isdigit() and mmr_change.startswith('+')):
                mmr_label.setStyleSheet("color: #51cf66;")
            elif '-' in mmr_change:
                mmr_label.setStyleSheet("color: #ff6b6b;")

            match_layout.addWidget(mmr_label)

            layout.addWidget(match_widget)

        return frame

    def create_pie_chart_section(self, sessions):
        """Create pie chart section showing goals/assists/saves distribution"""
        frame = QFrame()
        frame.setMinimumHeight(90)
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout = QVBoxLayout(frame)
        layout.setSpacing(3)
        layout.setContentsMargins(8, 6, 8, 6)

        # Section title
        title = QLabel("Match Stats Breakdown")
        title.setFont(QFont("Arial", 11, QFont.Bold))
        title.setStyleSheet("color: #ffffff !important; background-color: transparent;")
        title.setMinimumHeight(18)
        layout.addWidget(title)

        # Aggregate goals, assists, and saves from all sessions
        total_goals = 0
        total_assists = 0
        total_saves = 0

        for session in sessions:
            total_goals += session.get('goals', 0)
            total_assists += session.get('assists', 0)
            total_saves += session.get('saves', 0)

        # Create pie chart data
        pie_data = {
            'Goals': total_goals,
            'Assists': total_assists,
            'Saves': total_saves
        }

        # Create pie chart widget
        pie_chart = PieChartWidget(pie_data)
        pie_chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(pie_chart)

        return frame

    def create_lifetime_stats_section(self, lifetime_stats):
        """Create the lifetime stats section - compact"""
        frame = QFrame()
        frame.setMinimumHeight(80)  # Ensure frame is tall enough for title + stats row
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout = QVBoxLayout(frame)
        layout.setSpacing(3)
        layout.setContentsMargins(8, 6, 8, 6)

        # Section title
        title = QLabel("Lifetime Stats")
        title.setFont(QFont("Arial", 11, QFont.Bold))
        title.setStyleSheet("color: #ffffff !important; background-color: transparent;")
        title.setMinimumHeight(18)
        layout.addWidget(title)

        # Horizontal layout for stats (more compact)
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)

        # Display all lifetime stats (up to 7-8 should fit)
        for label, value in lifetime_stats.items():
            stat_widget = QWidget()
            stat_widget.setMinimumHeight(36)  # Ensure container is tall enough for content
            stat_vlayout = QVBoxLayout(stat_widget)
            stat_vlayout.setSpacing(1)
            stat_vlayout.setContentsMargins(0, 0, 0, 0)

            # Stat label
            label_widget = QLabel(label[:12])  # Truncate long labels
            label_widget.setFont(QFont("Arial", 8))
            label_widget.setStyleSheet("color: #999999;")
            label_widget.setAlignment(Qt.AlignCenter)
            label_widget.setMinimumHeight(14)
            stat_vlayout.addWidget(label_widget)

            # Stat value
            value_widget = QLabel(str(value))
            value_widget.setFont(QFont("Arial", 11, QFont.Bold))
            value_widget.setStyleSheet("color: #ffffff !important; background-color: transparent;")
            value_widget.setAlignment(Qt.AlignCenter)
            value_widget.setMinimumHeight(18)
            stat_vlayout.addWidget(value_widget)

            stats_layout.addWidget(stat_widget)

        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        return frame


def main():
    """Main entry point for the application"""
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    window = RLStatsApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
