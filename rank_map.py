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
        rank_text: Raw rank text (e.g., "Champion I Division II", "Champion III Div I")

    Returns:
        Path to the rank icon WEBP file. Returns None if not found.

    File naming convention:
        - Champion1_rank_icon.webp (Champion I)
        - Diamond3_rank_icon.webp (Diamond III)
        - Grand_champion2_rank_icon.webp (Grand Champion II)
        - Supersonic_Legend_rank_icon.webp
    """
    if not rank_text or rank_text.lower() == "unranked":
        return None  # No icon for unranked

    # Clean the rank text
    rank_lower = rank_text.lower()

    # Map Roman numerals to numbers (order matters - check longer patterns first!)
    roman_patterns = [
        (' iii ', '3'),  # Must check III before I
        (' ii ', '2'),   # Must check II before I
        (' iv ', '4'),
        (' v ', '5'),
        (' i ', '1'),    # Check I last
    ]

    # Extract rank tier and division
    # Examples: "Champion III Div I", "Diamond I Division II"

    # Handle special cases
    if "supersonic legend" in rank_lower:
        icon_path = RANK_ICON_DIR / "Supersonic_Legend_rank_icon.webp"
        if icon_path.exists():
            return icon_path

    # Handle Grand Champion
    if "grand champion" in rank_lower:
        # Extract the tier (I, II, III) - search for pattern right after "grand champion"
        # Pattern: "grand champion III" not "grand champion ... div I"
        gc_pattern = re.search(r'grand champion\s+(iii|ii|i(?!\w))', rank_lower)
        if gc_pattern:
            tier_roman = gc_pattern.group(1)
            for roman, num in roman_patterns:
                if tier_roman.strip() == roman.strip():
                    icon_path = RANK_ICON_DIR / f"Grand_champion{num}_rank_icon.webp"
                    if icon_path.exists():
                        return icon_path
                    break

    # Handle regular ranks (Bronze, Silver, Gold, Platinum, Diamond, Champion)
    ranks = ["champion", "diamond", "platinum", "gold", "silver", "bronze"]

    for rank in ranks:
        if rank in rank_lower:
            # Find the tier number RIGHT AFTER the rank name (not from division)
            # Pattern: "champion III" not "champion ... div I"
            rank_pattern = re.search(rf'{rank}\s+(iii|ii|i(?!\w))', rank_lower)
            if rank_pattern:
                tier_roman = rank_pattern.group(1)
                for roman, num in roman_patterns:
                    if tier_roman.strip() == roman.strip():
                        # Capitalize first letter of rank
                        rank_cap = rank.capitalize()
                        icon_path = RANK_ICON_DIR / f"{rank_cap}{num}_rank_icon.webp"
                        if icon_path.exists():
                            return icon_path
                        break
            break

    # If no match found, return None
    return None


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
