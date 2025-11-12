"""
Play Activity Heatmap for Rocket League Stats
Displays a GitHub-style activity graph showing match frequency
"""

from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QVBoxLayout, QHBoxLayout
from PySide6.QtGui import QColor, QPalette, QFont
from PySide6.QtCore import Qt
from datetime import datetime, timedelta
from collections import defaultdict


def parse_activity_data(matches):
    """
    Parse match data to count matches per day.

    Args:
        matches: List of match dictionaries with 'timestamp' or 'date' field

    Returns:
        dict: {date_str: match_count}
    """
    activity_counts = defaultdict(int)

    for match in matches:
        # Try to extract date from match
        date_str = None

        if 'date' in match:
            date_str = match['date']
        elif 'timestamp' in match:
            try:
                dt = datetime.fromisoformat(match['timestamp'])
                date_str = dt.strftime('%Y-%m-%d')
            except:
                pass

        if date_str:
            activity_counts[date_str] += 1

    return dict(activity_counts)


def build_heatmap_widget(activity_counts, days=30):
    """
    Build a heatmap widget showing play activity over the last N days.

    Args:
        activity_counts: dict with keys = date strings (YYYY-MM-DD), values = matches played
        days: Number of days to display (default: 30)

    Returns:
        QWidget: Widget containing the heatmap visualization
    """
    widget = QWidget()
    main_layout = QVBoxLayout(widget)
    main_layout.setSpacing(5)
    main_layout.setContentsMargins(0, 0, 0, 0)

    # Title
    title = QLabel("Play Activity (Last 30 Days)")
    title.setFont(QFont("Arial", 12, QFont.Bold))
    main_layout.addWidget(title)

    # Create grid for day squares
    grid_widget = QWidget()
    grid = QGridLayout(grid_widget)
    grid.setSpacing(2)
    grid.setContentsMargins(0, 0, 0, 0)

    # Calculate date range (last N days)
    today = datetime.now().date()
    date_list = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days-1, -1, -1)]

    # Find max activity for color scaling
    max_activity = max(activity_counts.values()) if activity_counts else 1
    if max_activity == 0:
        max_activity = 1

    # Create a square for each day
    squares_per_row = 10
    for i, date_str in enumerate(date_list):
        row = i // squares_per_row
        col = i % squares_per_row

        # Get activity count for this day
        count = activity_counts.get(date_str, 0)

        # Create label
        day_label = QLabel()
        day_label.setFixedSize(24, 24)
        day_label.setAutoFillBackground(True)

        # Calculate color intensity (orange scale: dark gray -> bright orange)
        if count == 0:
            # No activity - dark gray
            color = QColor(45, 45, 45)
        else:
            # Scale from dim orange to bright orange
            intensity = count / max_activity
            # Orange gradient: RGB (255, 140, 0) at full intensity
            red = 255
            green = int(50 + (140 - 50) * intensity)
            blue = 0
            color = QColor(red, green, blue)

        # Apply color
        pal = day_label.palette()
        pal.setColor(QPalette.Window, color)
        day_label.setPalette(pal)

        # Add border for better visibility
        day_label.setStyleSheet(f"""
            QLabel {{
                border: 1px solid #1a1a1a;
                border-radius: 3px;
            }}
        """)

        # Tooltip with date and count
        day_label.setToolTip(f"{date_str}\n{count} match{'es' if count != 1 else ''}")

        grid.addWidget(day_label, row, col)

    main_layout.addWidget(grid_widget)

    # Add legend
    legend_layout = QHBoxLayout()
    legend_layout.setSpacing(5)

    legend_label = QLabel("Less")
    legend_label.setFont(QFont("Arial", 8))
    legend_label.setStyleSheet("color: #999999;")
    legend_layout.addWidget(legend_label)

    # Legend squares
    legend_colors = [
        QColor(45, 45, 45),      # No activity
        QColor(255, 70, 0),      # Low
        QColor(255, 105, 0),     # Medium
        QColor(255, 140, 0),     # High
    ]

    for color in legend_colors:
        square = QLabel()
        square.setFixedSize(12, 12)
        square.setAutoFillBackground(True)
        pal = square.palette()
        pal.setColor(QPalette.Window, color)
        square.setPalette(pal)
        square.setStyleSheet("border: 1px solid #1a1a1a; border-radius: 2px;")
        legend_layout.addWidget(square)

    more_label = QLabel("More")
    more_label.setFont(QFont("Arial", 8))
    more_label.setStyleSheet("color: #999999;")
    legend_layout.addWidget(more_label)

    legend_layout.addStretch()
    main_layout.addLayout(legend_layout)

    return widget


# Example usage for testing
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    # Sample data
    sample_activity = {
        '2025-11-01': 5,
        '2025-11-02': 3,
        '2025-11-03': 0,
        '2025-11-04': 8,
        '2025-11-05': 2,
        '2025-11-08': 10,
        '2025-11-09': 4,
        '2025-11-10': 6,
        '2025-11-11': 1,
    }

    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    widget = build_heatmap_widget(sample_activity, days=30)
    widget.setStyleSheet("background-color: #1a1a1a; color: white;")
    widget.setFixedSize(400, 200)
    widget.show()

    sys.exit(app.exec())
