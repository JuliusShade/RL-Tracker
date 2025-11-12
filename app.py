"""
Rocket League Stats Display App
PySide6 GUI that displays stats from cached data
"""

import json
import sys
import yaml
from datetime import datetime
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QScrollArea, QPushButton, QGridLayout, QFrame
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QFont
from rank_map import rank_icon_path
from activity_map import parse_activity_data, build_heatmap_widget


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

        # Refresh button - compact
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_stats)
        refresh_btn.setMaximumWidth(120)
        refresh_btn.setMinimumHeight(30)
        refresh_btn.setFont(QFont("Arial", 10))

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(refresh_btn)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

    def apply_theme(self):
        """Apply color theme to the application"""
        if self.config['display']['theme'] == 'dark':
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #1a1a1a;
                    color: #ffffff;
                }
                QLabel {
                    color: #ffffff;
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
                QScrollArea {
                    border: none;
                    background-color: #1a1a1a;
                }
                QFrame {
                    background-color: #2d2d2d;
                    border-radius: 10px;
                    padding: 15px;
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
                    padding: 15px;
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
        """Clear all widgets from stats layout"""
        while self.stats_layout.count():
            child = self.stats_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

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

        # Create horizontal layout for ranks and activity
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        # Display rank information
        overview = data.get('overview', {})
        if overview:
            ranks_frame = self.create_ranks_section(overview)
            top_row.addWidget(ranks_frame, stretch=3)

        # Display activity heatmap
        matches = data.get('recent_matches', [])
        if matches:
            activity_data = parse_activity_data(matches)
            heatmap_widget = build_heatmap_widget(activity_data, days=30)
            top_row.addWidget(heatmap_widget, stretch=2)

        self.stats_layout.addLayout(top_row)

        # Display recent matches (compact)
        if matches:
            matches_frame = self.create_matches_section(matches)
            self.stats_layout.addWidget(matches_frame)

        # Display performance stats (compact)
        performance = data.get('performance', {})
        if performance:
            perf_frame = self.create_performance_section(performance)
            self.stats_layout.addWidget(perf_frame)

        # No stretch at the end for compact layout

    def create_ranks_section(self, overview):
        """Create the ranks display section - compact for Pi"""
        frame = QFrame()
        layout = QVBoxLayout(frame)
        layout.setSpacing(5)
        layout.setContentsMargins(8, 6, 8, 6)

        # Section title - compact
        title = QLabel("Ranks")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)

        # Vertical list for playlists (more compact than grid)
        for playlist_name, stats in overview.items():
            # Create playlist widget
            playlist_widget = QWidget()
            playlist_layout = QHBoxLayout(playlist_widget)
            playlist_layout.setSpacing(8)
            playlist_layout.setContentsMargins(0, 2, 0, 2)

            # Rank icon - smaller
            rank_text = stats.get('rank', 'Unranked')
            icon_file = rank_icon_path(rank_text)

            rank_icon = QLabel()
            if icon_file.exists():
                pixmap = QPixmap(str(icon_file))
                # Scale to smaller size for compact layout
                scaled_pixmap = pixmap.scaledToHeight(32, Qt.SmoothTransformation)
                rank_icon.setPixmap(scaled_pixmap)
                rank_icon.setFixedSize(32, 32)
            else:
                # Placeholder if icon doesn't exist
                rank_icon.setText("🏆")
                rank_icon.setFont(QFont("Arial", 16))
                rank_icon.setAlignment(Qt.AlignCenter)
                rank_icon.setFixedSize(32, 32)

            playlist_layout.addWidget(rank_icon)

            # Text info - horizontal for space efficiency
            # Playlist name
            name_label = QLabel(playlist_name[:12])  # Truncate if too long
            name_label.setFont(QFont("Arial", 9, QFont.Bold))
            name_label.setFixedWidth(80)
            playlist_layout.addWidget(name_label)

            # Rank
            rank_label = QLabel(rank_text)
            rank_label.setFont(QFont("Arial", 9))
            rank_label.setStyleSheet("color: #4ecdc4;")
            rank_label.setFixedWidth(100)
            playlist_layout.addWidget(rank_label)

            # MMR
            mmr = stats.get('mmr', 0)
            mmr_label = QLabel(f"{int(mmr)} MMR")
            mmr_label.setFont(QFont("Arial", 9))
            mmr_label.setAlignment(Qt.AlignRight)
            playlist_layout.addWidget(mmr_label)

            playlist_layout.addStretch()
            layout.addWidget(playlist_widget)

        return frame

    def create_matches_section(self, matches):
        """Create the recent matches section - compact"""
        frame = QFrame()
        layout = QVBoxLayout(frame)
        layout.setSpacing(3)
        layout.setContentsMargins(8, 6, 8, 6)

        # Section title
        title = QLabel("Recent Matches")
        title.setFont(QFont("Arial", 11, QFont.Bold))
        layout.addWidget(title)

        # Match list - show only top 3 for compact layout
        for i, match in enumerate(matches[:3], 1):
            match_widget = QWidget()
            match_layout = QHBoxLayout(match_widget)
            match_layout.setContentsMargins(0, 1, 0, 1)
            match_layout.setSpacing(6)

            # Result indicator (W/L)
            result = match.get('result', 'Unknown')
            result_short = "W" if 'Win' in result or 'Victory' in result else "L" if 'Loss' in result or 'Defeat' in result else "?"
            result_label = QLabel(result_short)
            result_label.setFont(QFont("Arial", 10, QFont.Bold))
            result_label.setFixedWidth(15)

            if result_short == "W":
                result_label.setStyleSheet("color: #51cf66;")
            elif result_short == "L":
                result_label.setStyleSheet("color: #ff6b6b;")

            match_layout.addWidget(result_label)

            # Playlist - shortened
            playlist = match.get('playlist', 'Unknown')
            playlist_short = playlist.replace('Ranked Doubles', '2v2').replace('Ranked Duel', '1v1').replace('Ranked Standard', '3v3')
            playlist_label = QLabel(playlist_short[:10])
            playlist_label.setFont(QFont("Arial", 9))
            playlist_label.setFixedWidth(60)
            match_layout.addWidget(playlist_label)

            match_layout.addStretch()

            # MMR change
            mmr_change = match.get('mmr_change', '0')
            mmr_label = QLabel(mmr_change)
            mmr_label.setFont(QFont("Arial", 9, QFont.Bold))
            if '+' in mmr_change or (mmr_change.replace('.', '').replace('-', '').isdigit() and mmr_change.startswith('+')):
                mmr_label.setStyleSheet("color: #51cf66;")
            elif '-' in mmr_change:
                mmr_label.setStyleSheet("color: #ff6b6b;")

            match_layout.addWidget(mmr_label)

            layout.addWidget(match_widget)

        return frame

    def create_performance_section(self, performance):
        """Create the performance metrics section - compact"""
        frame = QFrame()
        layout = QVBoxLayout(frame)
        layout.setSpacing(3)
        layout.setContentsMargins(8, 6, 8, 6)

        # Section title
        title = QLabel("Performance")
        title.setFont(QFont("Arial", 11, QFont.Bold))
        layout.addWidget(title)

        # Horizontal layout for stats (more compact)
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)

        # Limit to top 4 most important stats
        count = 0
        max_stats = 4
        for label, value in performance.items():
            if count >= max_stats:
                break

            stat_widget = QWidget()
            stat_vlayout = QVBoxLayout(stat_widget)
            stat_vlayout.setSpacing(1)
            stat_vlayout.setContentsMargins(0, 0, 0, 0)

            # Stat label
            label_widget = QLabel(label[:12])  # Truncate long labels
            label_widget.setFont(QFont("Arial", 8))
            label_widget.setStyleSheet("color: #999999;")
            label_widget.setAlignment(Qt.AlignCenter)
            stat_vlayout.addWidget(label_widget)

            # Stat value
            value_widget = QLabel(str(value))
            value_widget.setFont(QFont("Arial", 11, QFont.Bold))
            value_widget.setAlignment(Qt.AlignCenter)
            stat_vlayout.addWidget(value_widget)

            stats_layout.addWidget(stat_widget)
            count += 1

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
