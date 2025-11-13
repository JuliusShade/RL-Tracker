"""
BeautifulSoup-based HTML Parser for Rocket League Tracker
Issue #4 Implementation - Intelligently parses saved HTML files
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from bs4 import BeautifulSoup
from collections import defaultdict


class RLStatsParser:
    """Intelligent HTML parser for Rocket League stats"""

    def __init__(self, html_dir="data/html", output_file="rl_stats.json"):
        self.html_dir = Path(__file__).parent / html_dir
        self.output_file = Path(__file__).parent / output_file

    def load_html(self, filename):
        """Load HTML file and return BeautifulSoup object"""
        file_path = self.html_dir / f"{filename}.html"

        if not file_path.exists():
            print(f"[WARNING] HTML file not found: {filename}.html")
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html = f.read()
            return BeautifulSoup(html, 'html.parser')
        except Exception as e:
            print(f"[ERROR] Failed to load {filename}.html: {e}")
            return None

    def extract_ranks(self, soup):
        """Extract rank information from overview page"""
        print("\n>> Parsing ranks from overview.html...")
        ranks = {}

        if not soup:
            return ranks

        # Get all text as one big string (easier for parsing this format)
        full_text = soup.get_text()

        # Pattern: "Ranked [Type] [MMR]Div[numbers][Rank Name with Division]"
        # Example: "Ranked Doubles 2v2 1,308Div257Champion III Div I"

        playlists = [
            ('Ranked Duel 1v1', 'Ranked Duel 1v1'),
            ('Ranked Doubles 2v2', 'Ranked Doubles 2v2'),
            ('Ranked Standard 3v3', 'Ranked Standard 3v3'),
            ('Hoops', 'Hoops'),
            ('Rumble', 'Rumble'),
            ('Dropshot', 'Dropshot'),
            ('Snowday', 'Snow Day')
        ]

        for pattern, playlist_name in playlists:
            try:
                # Find the playlist in text
                if pattern not in full_text:
                    continue

                # Look for pattern with current rating
                # Format: "Ranked Doubles 2v2 1,308Div257Champion III Div I"
                # The pattern matches: playlist + MMR + "Div" stuff + rank name
                pattern_with_div = rf'{re.escape(pattern)}\s+(\d{{1,4}}(?:,\d{{3}})?)[Div\d\s]*?((?:Supersonic Legend|Grand Champion|Champion|Diamond|Platinum|Gold|Silver|Bronze)\s+(?:I{{1,3}}|IV|V)\s+Div\s+(?:I{{1,3}}|IV|V))'

                match = re.search(pattern_with_div, full_text)

                if not match:
                    # Fallback: try simpler pattern
                    pos = full_text.find(pattern)
                    chunk = full_text[pos:pos+200]
                    mmr_match = re.search(rf'{re.escape(pattern)}\s*(\d{{1,4}}(?:,\d{{3}})?)', chunk)
                    mmr = 0
                    if mmr_match:
                        mmr_str = mmr_match.group(1).replace(',', '')
                        mmr = int(mmr_str)

                    rank_pattern = r'((?:Supersonic Legend|Grand Champion|Champion|Diamond|Platinum|Gold|Silver|Bronze)\s+(?:I{1,3}|IV|V)?\s*(?:Div\s+(?:I{1,3}|IV|V))?)'
                    rank_match = re.search(rank_pattern, chunk)
                    rank = "Unranked"
                    if rank_match:
                        rank = rank_match.group(1).strip()
                        rank = re.sub(r'\s+', ' ', rank)
                else:
                    # Extract from the combined match
                    mmr_str = match.group(1).replace(',', '')
                    mmr = int(mmr_str)
                    rank = match.group(2).strip()
                    rank = re.sub(r'\s+', ' ', rank)

                # Store the data
                if rank != "Unranked" or mmr > 0:
                    ranks[playlist_name] = {
                        'rank': rank,
                        'mmr': mmr
                    }
                    print(f"   [OK] {playlist_name}: {rank} ({mmr} MMR)")

            except Exception as e:
                print(f"   ! Error parsing {playlist_name}: {e}")
                continue

        print(f"\n   Total: {len(ranks)} ranked playlists")
        return ranks

    def extract_matches(self, soup):
        """Extract session-grouped match history from matches/overview page"""
        print("\n>> Parsing session-grouped matches...")
        sessions = []
        heatmap_data = defaultdict(int)  # date -> match_count

        if not soup:
            return sessions, heatmap_data

        full_text = soup.get_text()

        # Pattern: Session Overview [time_ago] [details]... [matches]
        session_pattern = r'Session Overview\s+(\d+\s+(?:hours?|days?|weeks?|months?)\s+ago)(.*?)(?=Session Overview|Get the Mobile|Premium users|$)'
        session_matches = re.findall(session_pattern, full_text, re.DOTALL | re.IGNORECASE)

        print(f"   Found {len(session_matches)} gaming sessions")

        for time_ago, details in session_matches[:20]:  # Limit to 20 sessions
            try:
                session_date = self._parse_relative_date(time_ago)

                # Extract wins/losses
                wins = 0
                losses = 0
                wins_match = re.search(r'(\d+)\s+Wins?', details)
                if wins_match:
                    wins = int(wins_match.group(1))

                # Extract match counts by playlist
                # Pattern: "9 Matches Ranked Standard 3v3 1,096" or "9 Matches Ranked Duel 1v1 823"
                # Note: Sometimes "Saves 249 Matches" where 24=saves, 9=matches (no space)
                # MMR format: Either "1,234" (with comma) or "123" (3 digits without comma)
                # Avoid matching "823121" as MMR (should be just "823")
                match_counts = re.findall(r'(\d{1,2})(?:\s+Match(?:es)?)\s+(Ranked\s+(?:Duel|Doubles|Standard|4v4\s+Quads?)\s+\dv\d)\s*(\d{1,3}(?:,\d{3})?)', details)

                # Extract stats
                goals_shots = re.search(r'Goals\s*/\s*Shots\s+(\d+)\s*/\s*(\d+)', details)
                assists = re.search(r'Assists\s+(\d+)', details)
                saves = re.search(r'Saves\s+(\d+)', details)
                mvp = re.search(r'MVP\s*\((\d+)\)', details)

                # Build session object
                session = {
                    'time_ago': time_ago,
                    'date': session_date,
                    'wins': wins,
                    'matches': []
                }

                if goals_shots:
                    session['goals'] = int(goals_shots.group(1))
                    session['shots'] = int(goals_shots.group(2))
                if assists:
                    session['assists'] = int(assists.group(1))
                if saves:
                    session['saves'] = int(saves.group(1))
                if mvp:
                    session['mvp_count'] = int(mvp.group(1))

                # Add individual matches from this session
                total_matches = 0
                for count_str, playlist, mmr_str in match_counts:
                    count = int(count_str)
                    total_matches += count

                    # Normalize playlist name
                    playlist = playlist.strip()
                    if 'Standard' in playlist or '3v3' in playlist:
                        playlist = "Ranked Standard 3v3"
                    elif 'Doubles' in playlist or '2v2' in playlist:
                        playlist = "Ranked Doubles 2v2"
                    elif 'Duel' in playlist or '1v1' in playlist:
                        playlist = "Ranked Duel 1v1"

                    mmr = int(mmr_str.replace(',', ''))

                    session['matches'].append({
                        'count': count,
                        'playlist': playlist,
                        'mmr': mmr
                    })

                # Update heatmap data
                if session_date and total_matches > 0:
                    heatmap_data[session_date] += total_matches

                # Only add session if it has matches
                if session['matches']:
                    sessions.append(session)

            except Exception as e:
                print(f"   ! Error parsing session: {e}")
                continue

        print(f"   Extracted {len(sessions)} valid sessions")
        print(f"   Heatmap covers {len(heatmap_data)} unique days")

        # Convert heatmap to list format for JSON
        heatmap_list = [{'date': date, 'count': count} for date, count in sorted(heatmap_data.items())]

        return sessions, heatmap_list

    def extract_performance(self, soup):
        """Extract performance statistics"""
        print("\n>> Parsing performance from performance.html...")
        performance = {}

        if not soup:
            return performance

        # Performance stats we're looking for
        stat_keywords = [
            'Goals', 'Assists', 'Saves', 'Shots', 'Win Rate', 'MVPs',
            'Goal Shot Ratio', 'Score', 'Shooting %', 'Save %'
        ]

        all_elements = soup.find_all(['div', 'span', 'td', 'li'])

        for element in all_elements:
            try:
                text = element.get_text(" ", strip=True)

                # Check if text contains any stat keyword
                for keyword in stat_keywords:
                    if keyword in text and keyword not in performance:
                        # Try to extract the value (number, percentage, or ratio)
                        value_match = re.search(r'(\d+(?:\.\d+)?%?)', text)
                        if value_match:
                            value = value_match.group(1)
                            performance[keyword] = value

            except Exception as e:
                continue

        print(f"   Found {len(performance)} performance stats")
        for stat, value in list(performance.items())[:5]:
            print(f"   - {stat}: {value}")

        return performance

    def _parse_absolute_date(self, date_str):
        """Parse absolute date string to YYYY-MM-DD"""
        try:
            formats = [
                '%m/%d/%Y',
                '%Y-%m-%d',
                '%d/%m/%Y',
                '%b %d, %Y',
                '%B %d, %Y'
            ]

            for fmt in formats:
                try:
                    dt = datetime.strptime(date_str.strip(), fmt)
                    return dt.strftime('%Y-%m-%d')
                except:
                    continue

            return None
        except:
            return None

    def _parse_relative_date(self, relative_str):
        """Parse relative date like '2 days ago'"""
        try:
            text = relative_str.lower()
            today = datetime.now()

            # Extract number
            match = re.search(r'(\d+)', text)
            if not match:
                return today.strftime('%Y-%m-%d')

            num = int(match.group(1))

            if 'hour' in text:
                # Same day
                return today.strftime('%Y-%m-%d')
            elif 'day' in text:
                dt = today - timedelta(days=num)
                return dt.strftime('%Y-%m-%d')
            elif 'week' in text:
                dt = today - timedelta(weeks=num)
                return dt.strftime('%Y-%m-%d')

            return today.strftime('%Y-%m-%d')
        except:
            return None

    def extract_lifetime_stats(self, soup):
        """Extract lifetime statistics from overview page"""
        print("\n>> Parsing lifetime stats from overview.html...")
        lifetime = {}

        if not soup:
            return lifetime

        full_text = soup.get_text()

        # Lifetime stats on overview are in format: "StatName[value]#[rank] • Top/Bottom [percentage]%"
        # Example: "Wins2,260#2,449,599 • Top 36.0%" or "Goal Shot Ratio48.5#9,633,706 • Bottom 27.0%"
        stat_patterns = {
            'Wins': r'Lifetime\s+Wins(\d{1,3}(?:,\d{3})*)#',
            'Goals': r'(?<!\w)Goals(\d{1,3}(?:,\d{3})*)#',  # Negative lookbehind to avoid matching "Goals / Shots"
            'Assists': r'(?<!\w)Assists(\d{1,3}(?:,\d{3})*)#',
            'Saves': r'(?<!\w)Saves(\d{1,3}(?:,\d{3})*)#',
            'Shots': r'(?<!\w)Shots(\d{1,3}(?:,\d{3})*)#',
            'MVPs': r'MVPs(\d{1,3}(?:,\d{3})*)#',
            'Goal Shot Ratio': r'Goal\s+Shot\s+Ratio([\d.]+)#',
            'TRN Score': r'TRN\s+Score([\d,]+\.?\d*)#',
        }

        for stat_name, pattern in stat_patterns.items():
            try:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    value = match.group(1)
                    # Add % for Goal Shot Ratio
                    if stat_name == 'Goal Shot Ratio' and '%' not in value:
                        value = f"{value}%"
                    lifetime[stat_name] = value
                    print(f"   [OK] {stat_name}: {value}")
            except Exception as e:
                continue

        print(f"\n   Total: {len(lifetime)} lifetime stats")
        return lifetime

    def parse_all(self):
        """Parse all HTML files and generate rl_stats.json"""
        print("\n" + "="*60)
        print("STARTING BEAUTIFULSOUP HTML PARSER")
        print("="*60)

        # Load only overview HTML (contains all needed data)
        overview_soup = self.load_html('overview')

        if not overview_soup:
            print("\n[ERROR] Could not load overview.html")
            return False

        # Parse each section from overview
        overview_data = self.extract_ranks(overview_soup)

        # Extract sessions and heatmap from overview
        sessions_data, heatmap_data = self.extract_matches(overview_soup)

        # Extract lifetime stats from overview
        lifetime_stats = self.extract_lifetime_stats(overview_soup)
        if lifetime_stats:
            overview_data['__lifetime__'] = lifetime_stats

        # Performance data no longer used (lifetime stats replace it)
        performance_data = {}

        # Combine into output format
        output = {
            'timestamp': datetime.now().isoformat(),
            'overview': overview_data,
            'sessions': sessions_data,  # Session-grouped matches
            'activity_heatmap': heatmap_data,  # Date -> match count
            'performance': performance_data
        }

        # Save to JSON
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2)

            print("\n" + "="*60)
            print(f"[SUCCESS] Stats saved to {self.output_file}")
            print("="*60)
            print(f"\nSummary:")
            print(f"  Playlists: {len(overview_data)}")
            print(f"  Sessions: {len(sessions_data)}")
            print(f"  Heatmap Days: {len(heatmap_data)}")
            print(f"  Performance Stats: {len(performance_data)}")

            if sessions_data:
                total_matches = sum(sum(m['count'] for m in s.get('matches', [])) for s in sessions_data)
                print(f"  Total Matches: {total_matches}")
            print()

            return True

        except Exception as e:
            print(f"\n[ERROR] Failed to save {self.output_file}: {e}")
            import traceback
            traceback.print_exc()
            return False


def parse_all():
    """Main entry point for parser"""
    parser = RLStatsParser()
    return parser.parse_all()


if __name__ == "__main__":
    parse_all()
