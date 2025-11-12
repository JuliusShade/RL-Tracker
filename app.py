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


class RLStatsApp(QMainWindow):
    """Main application window for RL Stats Display"""

    def __init__(self):
        super().__init__()
        self.config = self._load_config()
        self.cache_path = Path(self.config['cache']['path']).expanduser()

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
        self.setWindowTitle("Rocket League Stats Tracker")

        # Set window size from config
        width = self.config['display']['window_width']
        height = self.config['display']['window_height']
        self.setGeometry(100, 100, width, height)

        # Apply theme
        self.apply_theme()

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel("Rocket League Stats Dashboard")
        header.setFont(QFont("Arial", 24, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)

        # Player info
        self.player_label = QLabel()
        self.player_label.setFont(QFont("Arial", 14))
        self.player_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.player_label)

        # Last updated label
        self.updated_label = QLabel("Last updated: Never")
        self.updated_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.updated_label)

        # Scroll area for stats
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        self.stats_layout = QVBoxLayout(scroll_content)
        self.stats_layout.setSpacing(15)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        # Refresh button
        refresh_btn = QPushButton("Refresh Stats")
        refresh_btn.clicked.connect(self.load_stats)
        refresh_btn.setMaximumWidth(200)
        refresh_btn.setMinimumHeight(40)

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
        self.player_label.setText(f"Player: {username} ({platform.upper()})")

        # Update timestamp
        timestamp = data.get('timestamp', '')
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                self.updated_label.setText(f"Last updated: {formatted_time}")
            except:
                self.updated_label.setText(f"Last updated: {timestamp}")

        # Display rank information
        overview = data.get('overview', {})
        if overview:
            ranks_frame = self.create_ranks_section(overview)
            self.stats_layout.addWidget(ranks_frame)

        # Display recent matches
        matches = data.get('recent_matches', [])
        if matches:
            matches_frame = self.create_matches_section(matches)
            self.stats_layout.addWidget(matches_frame)

        # Display performance stats
        performance = data.get('performance', {})
        if performance:
            perf_frame = self.create_performance_section(performance)
            self.stats_layout.addWidget(perf_frame)

        # Add stretch at the end
        self.stats_layout.addStretch()

    def create_ranks_section(self, overview):
        """Create the ranks display section"""
        frame = QFrame()
        layout = QVBoxLayout(frame)

        # Section title
        title = QLabel("Current Ranks")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(title)

        # Grid for playlists
        grid = QGridLayout()
        grid.setSpacing(15)

        row = 0
        col = 0
        max_cols = 2

        for playlist_name, stats in overview.items():
            # Create playlist widget
            playlist_widget = QWidget()
            playlist_layout = QHBoxLayout(playlist_widget)
            playlist_layout.setSpacing(10)

            # Rank icon
            rank_text = stats.get('rank', 'Unranked')
            icon_file = rank_icon_path(rank_text)

            rank_icon = QLabel()
            if icon_file.exists():
                pixmap = QPixmap(str(icon_file))
                # Scale to reasonable size
                scaled_pixmap = pixmap.scaledToHeight(48, Qt.SmoothTransformation)
                rank_icon.setPixmap(scaled_pixmap)
                rank_icon.setFixedSize(48, 48)
            else:
                # Placeholder if icon doesn't exist
                rank_icon.setText("🏆")
                rank_icon.setFont(QFont("Arial", 24))
                rank_icon.setAlignment(Qt.AlignCenter)
                rank_icon.setFixedSize(48, 48)

            playlist_layout.addWidget(rank_icon)

            # Text info (vertical layout)
            text_widget = QWidget()
            text_layout = QVBoxLayout(text_widget)
            text_layout.setSpacing(2)
            text_layout.setContentsMargins(0, 0, 0, 0)

            # Playlist name
            name_label = QLabel(playlist_name)
            name_label.setFont(QFont("Arial", 11, QFont.Bold))
            text_layout.addWidget(name_label)

            # Rank
            rank_label = QLabel(rank_text)
            rank_label.setFont(QFont("Arial", 12))
            rank_label.setStyleSheet("color: #4ecdc4;")
            text_layout.addWidget(rank_label)

            # MMR
            mmr = stats.get('mmr', 0)
            mmr_label = QLabel(f"MMR: {mmr}")
            mmr_label.setFont(QFont("Arial", 10))
            text_layout.addWidget(mmr_label)

            playlist_layout.addWidget(text_widget)
            playlist_layout.addStretch()

            grid.addWidget(playlist_widget, row, col)

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        layout.addLayout(grid)
        return frame

    def create_matches_section(self, matches):
        """Create the recent matches section"""
        frame = QFrame()
        layout = QVBoxLayout(frame)

        # Section title
        title = QLabel("Recent Matches")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(title)

        # Match list
        for i, match in enumerate(matches[:5], 1):  # Show top 5
            match_widget = QWidget()
            match_layout = QHBoxLayout(match_widget)
            match_layout.setContentsMargins(10, 5, 10, 5)

            # Match number
            num_label = QLabel(f"#{i}")
            num_label.setFixedWidth(30)
            match_layout.addWidget(num_label)

            # Result
            result = match.get('result', 'Unknown')
            result_label = QLabel(result)
            result_label.setFont(QFont("Arial", 12, QFont.Bold))
            result_label.setFixedWidth(80)

            if 'Win' in result or 'Victory' in result:
                result_label.setStyleSheet("color: #51cf66;")
            elif 'Loss' in result or 'Defeat' in result:
                result_label.setStyleSheet("color: #ff6b6b;")

            match_layout.addWidget(result_label)

            # Playlist
            playlist = match.get('playlist', 'Unknown')
            playlist_label = QLabel(playlist)
            playlist_label.setFont(QFont("Arial", 11))
            match_layout.addWidget(playlist_label)

            match_layout.addStretch()

            # MMR change
            mmr_change = match.get('mmr_change', '0')
            mmr_label = QLabel(mmr_change)
            mmr_label.setFont(QFont("Arial", 11, QFont.Bold))
            if '+' in mmr_change or (mmr_change.replace('.', '').isdigit() and float(mmr_change) > 0):
                mmr_label.setStyleSheet("color: #51cf66;")
            elif '-' in mmr_change:
                mmr_label.setStyleSheet("color: #ff6b6b;")

            match_layout.addWidget(mmr_label)

            layout.addWidget(match_widget)

        return frame

    def create_performance_section(self, performance):
        """Create the performance metrics section"""
        frame = QFrame()
        layout = QVBoxLayout(frame)

        # Section title
        title = QLabel("Performance Metrics")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(title)

        # Grid for stats
        grid = QGridLayout()
        grid.setSpacing(10)

        row = 0
        col = 0
        max_cols = 3

        for label, value in performance.items():
            stat_widget = QWidget()
            stat_layout = QVBoxLayout(stat_widget)
            stat_layout.setSpacing(2)

            # Stat label
            label_widget = QLabel(label)
            label_widget.setFont(QFont("Arial", 10))
            label_widget.setStyleSheet("color: #999999;")
            stat_layout.addWidget(label_widget)

            # Stat value
            value_widget = QLabel(str(value))
            value_widget.setFont(QFont("Arial", 14, QFont.Bold))
            stat_layout.addWidget(value_widget)

            grid.addWidget(stat_widget, row, col)

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        layout.addLayout(grid)
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
