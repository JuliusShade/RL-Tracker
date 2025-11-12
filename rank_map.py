"""
Rank Icon Mapping for Rocket League
Maps rank text to icon file paths
"""
import re
from pathlib import Path

RANK_ICON_DIR = Path("assets/ranks")


def normalize_rank_name(rank_text: str) -> str:
    """
    Normalize rank text to a standardized format for icon lookup.

    Args:
        rank_text: Raw rank text (e.g., "Champion I Division II")

    Returns:
        Normalized rank name (e.g., "champion_i")
    """
    if not rank_text:
        return "unranked"

    # Convert to lowercase
    t = rank_text.lower()

    # Remove division info in parentheses
    t = re.sub(r"\(.*?\)", "", t)

    # Remove "division" keyword
    t = t.replace("division", "").strip()

    # Define rank tiers in order
    tiers = [
        "supersonic legend",
        "grand champion iii",
        "grand champion ii",
        "grand champion i",
        "champion iii",
        "champion ii",
        "champion i",
        "diamond iii",
        "diamond ii",
        "diamond i",
        "platinum iii",
        "platinum ii",
        "platinum i",
        "gold iii",
        "gold ii",
        "gold i",
        "silver iii",
        "silver ii",
        "silver i",
        "bronze iii",
        "bronze ii",
        "bronze i",
        "unranked"
    ]

    # Find matching tier
    for tier in tiers:
        if tier in t:
            # Replace spaces with underscores
            return tier.replace(" ", "_")

    return "unranked"


def rank_icon_path(rank_text: str) -> Path:
    """
    Get the file path for a rank icon based on rank text.

    Args:
        rank_text: Raw rank text (e.g., "Champion I Division II")

    Returns:
        Path to the rank icon PNG file. Falls back to unranked.png if not found.
    """
    # Normalize the rank name
    key = normalize_rank_name(rank_text)

    # Try exact match first
    png = RANK_ICON_DIR / f"{key}.png"
    if png.exists():
        return png

    # Try base rank without division (e.g., "champion" instead of "champion_i")
    base = key.split("_")[0]
    fb = RANK_ICON_DIR / f"{base}.png"
    if fb.exists():
        return fb

    # Fall back to unranked
    return RANK_ICON_DIR / "unranked.png"


# Example usage
if __name__ == "__main__":
    # Test cases
    test_ranks = [
        "Champion I Division II",
        "Diamond II Division III",
        "Grand Champion III",
        "Supersonic Legend",
        "Gold I",
        "Bronze III Division IV",
        "Unranked",
        "",
    ]

    print("Testing rank normalization:")
    for rank in test_ranks:
        normalized = normalize_rank_name(rank)
        icon_path = rank_icon_path(rank)
        print(f"  '{rank}' -> '{normalized}' -> {icon_path}")
