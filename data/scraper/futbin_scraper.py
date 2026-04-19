"""
Futbin FC26 player scraper.

Scrapes player listing pages from Futbin and generates a CSV compatible
with the SBC solver's expected 69-column semicolon-delimited format.

Usage:
    python -m data.scraper.futbin_scraper [--pages N] [--output PATH] [--delay SEC]

Notes:
    - Futbin individual player pages are blocked by Cloudflare (403).
    - Only listing page data is available: Name, Rating, Position, Price,
      Version, Nationality, League, Club, DefId, Slug.
    - Detailed stats (Acceleration, Finishing, etc.) are filled with 0.
      If you need stats, merge with a Kaggle dataset after scraping.
"""

import argparse
import csv
import pathlib
import re
import time

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.futbin.com/players"

# Order must match the 69-column template exactly.
CSV_COLUMNS = [
    # GeneralCardData (21)
    "Name", "Version", "Club", "League", "Nationality", "Alt Pos.",
    "Skill Moves", "Weak Foot", "Foot", "Att W/R", "Def W/R",
    "Age", "Height", "Weight", "Body Type", "Added", "Price",
    "Position", "ID", "Overall Rating", "Futwiz Link",
    # CommonPosStats (37)
    "PAC", "AcceleRATE", "Acceleration", "Sprint Speed",
    "SHO", "Positioning", "Finishing", "Shot Power", "Long Shots",
    "Volleys", "Penalties",
    "PAS", "Vision", "Crossing", "FK. Acc.", "Short Pass", "Long Pass",
    "Curve",
    "DRI", "Agility", "Balance", "Reactions", "Ball Control",
    "Dribbling", "Composure",
    "DEF", "Interceptions", "Heading Acc.", "Def. Awareness",
    "Stand Tackle", "Slide Tackle",
    "PHY", "Jumping", "Stamina", "Strength", "Aggression",
    "PlayStyles+", "PlayStyles",
    # GkPosStats (11)
    "DIV", "GK. Diving", "REF", "GK. Reflexes", "HAN", "GK. Handling",
    "SPD", "KIC", "GK. Kicking", "POS", "GK. Pos",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# Price string -> int helpers
PRICE_MULTIPLIERS = {"K": 1_000, "M": 1_000_000}


def parse_price(price_str: str) -> int:
    """Convert Futbin price string like '1.2K' or '350' to integer."""
    if not price_str:
        return 0
    price_str = price_str.strip().replace(",", "")
    if not price_str:
        return 0
    try:
        upper = price_str.upper()
        for suffix, mult in PRICE_MULTIPLIERS.items():
            if upper.endswith(suffix):
                return int(float(upper[:-1]) * mult)
        return int(float(price_str))
    except ValueError:
        return 0


def build_futwiz_link(slug: str, def_id: str) -> str:
    """Construct a Futwiz player link from slug and DefId."""
    if slug and def_id:
        return f"https://www.futwiz.com/en/fc26/player/{slug}/{def_id}"
    return ""


def _extract_player_link_data(name_cell) -> tuple[str, str, str]:
    """Extract Name, DefId, Slug from the player link in the name cell.

    Futbin name cells contain TWO links to the same player page:
      <a href="/26/player/21745/ousmane-dembele">97</a>           ← rating (numeric)
      <a href="/26/player/21745/ousmane-dembele">Ousmane Dembélé</a> ← name

    We skip links whose text is purely numeric (ratings) and return the
    first non-numeric player link's text as the name.
    """
    for link in name_cell.find_all("a", href=True):
        href = link["href"]
        if "/player/" in href:
            text = link.get_text(strip=True)
            if not text or any(q in href for q in ("club=", "nation=", "league=", "playstyle=")):
                continue
            # Skip rating links — they contain only digits
            if text.isdigit():
                def_id, slug = _parse_player_href(href)
                continue  # keep def_id/slug from this link, but skip name
            def_id, slug = _parse_player_href(href)
            return text, def_id, slug
    # Fallback: if only a numeric link was found, return def_id/slug with empty name
    for link in name_cell.find_all("a", href=True):
        href = link["href"]
        if "/player/" in href and not any(q in href for q in ("club=", "nation=", "league=", "playstyle=")):
            def_id, slug = _parse_player_href(href)
            return link.get_text(strip=True), def_id, slug
    return "", "", ""


def _parse_player_href(href: str) -> tuple[str, str]:
    """Extract DefId and Slug from a Futbin player href."""
    parts = href.strip("/").split("/")
    # parts e.g. ['26', 'player', '21745', 'ousmane-dembele']
    if len(parts) >= 4:
        return parts[-2], parts[-1]
    elif len(parts) == 3:
        return parts[-2], parts[-1]
    return "", ""


def _extract_from_query_links(name_cell) -> tuple[str, str, str]:
    """Extract Club, Nationality, League from query-param links in name cell.

    Links look like:
      <a href="/players?club=73"><img alt="FC Barcelona" ...></a>
      <a href="/players?nation=18"><img alt="France" ...></a>
      <a href="/players?league=16"><img alt="LaLiga" ...></a>
    """
    club = nationality = league = ""
    for link in name_cell.find_all("a", href=True):
        href = link["href"]
        if "club=" in href:
            img = link.find("img")
            # Prefer img title (real name) over alt (generic "Club")
            if img:
                club = img.get("title", "") or img.get("alt", "")
            if not club:
                club = link.get("title", "")
        elif "nation=" in href:
            img = link.find("img")
            if img:
                nationality = img.get("title", "") or img.get("alt", "")
            if not nationality:
                nationality = link.get("title", "")
        elif "league=" in href:
            img = link.find("img")
            if img:
                league = img.get("title", "") or img.get("alt", "")
            if not league:
                league = link.get("title", "")
    return club, nationality, league


def _clean_stat(text: str) -> int:
    """Parse a stat string like '97' or '--' to int (0 if missing)."""
    text = text.strip().replace(",", "")
    try:
        return int(text)
    except ValueError:
        return 0


def scrape_page(page_num: int, session: requests.Session) -> list[dict]:
    """Scrape a single Futbin players listing page and return player dicts.

    Futbin HTML structure (19 columns per row):
      td[0]  table-name      — name, club, nation, league links, playstyles
      td[1]  table-rating    — overall rating
      td[2]  table-pos       — position
      td[3]  table-price ps  — PS price
      td[4]  table-price pc  — PC price
      td[5]                  — stats + version info
      td[6]  table-foot      — foot preference
      td[7]  table-skills    — skill moves
      td[8]  table-weak-foot — weak foot
      td[9]  table-pace      — PAC
      td[10] table-shooting  — SHO
      td[11] table-passing   — PAS
      td[12] table-dribbling — DRI
      td[13] table-defending — DEF
      td[14] table-physicality — PHY
      td[15] table-popularity
      td[16] table-in-game-stats
      td[17] table-height    — height + AcceleRATE
      td[18] (empty/unknown)
    """
    url = f"{BASE_URL}?page={page_num}"
    resp = session.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table", class_="players-table")
    if not table:
        return []

    players = []
    rows = table.find("tbody").find_all("tr") if table.find("tbody") else table.find_all("tr", class_="player-row")

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 15:
            continue

        player = {}

        # td[0] — Name, DefId, Slug, Club, Nation, League
        name_cell = cols[0]
        name, def_id, slug = _extract_player_link_data(name_cell)
        club, nationality, league = _extract_from_query_links(name_cell)

        player["Name"] = name
        player["DefId"] = def_id
        player["Slug"] = slug
        player["Club"] = club
        player["Nationality"] = nationality
        player["League"] = league

        # td[1] — Overall Rating
        player["Overall Rating"] = cols[1].get_text(strip=True)

        # td[2] — Position (may contain "ST++CAM, RW" — take first part)
        pos_text = cols[2].get_text(strip=True)
        # Keep just the primary position (before commas or ++)
        if "," in pos_text:
            pos_text = pos_text.split(",")[0].strip()
        if "++" in pos_text:
            pos_text = pos_text.split("++")[0].strip()
        if "+" in pos_text and len(pos_text) > 3:
            pos_text = pos_text.split("+")[0].strip()
        player["Position"] = pos_text

        # td[3] — PS price (preferred), td[4] — PC price (fallback)
        price_text = cols[3].get_text(strip=True) if len(cols) > 3 else ""
        if not price_text or price_text == "--":
            price_text = cols[4].get_text(strip=True) if len(cols) > 4 else ""
        # Remove trailing percentage like "5.59%"
        if "%" in price_text:
            price_text = price_text.split("%")[0]
            m = re.match(r"^([\d.,]+[KM]?)", price_text.strip())
            if m:
                price_text = m.group(1)
        player["Price"] = parse_price(price_text)

        # td[5] — Stats + Version info (e.g. "95.1RW- IF")
        stats_version = cols[5].get_text(strip=True) if len(cols) > 5 else ""
        # Extract version (usually after the dash, e.g. "IF", "TOTW", "Gold")
        version = ""
        if "-" in stats_version:
            parts = stats_version.split("-")
            if len(parts) >= 2:
                version = parts[-1].strip()
        player["Version"] = version

        # td[6] — Foot
        player["Foot"] = cols[6].get_text(strip=True) if len(cols) > 6 else ""

        # td[7] — Skill Moves
        player["Skill Moves"] = cols[7].get_text(strip=True) if len(cols) > 7 else "0"

        # td[8] — Weak Foot
        player["Weak Foot"] = cols[8].get_text(strip=True) if len(cols) > 8 else "0"

        # td[9-14] — Stats
        player["PAC"] = _clean_stat(cols[9].get_text(strip=True)) if len(cols) > 9 else 0
        player["SHO"] = _clean_stat(cols[10].get_text(strip=True)) if len(cols) > 10 else 0
        player["PAS"] = _clean_stat(cols[11].get_text(strip=True)) if len(cols) > 11 else 0
        player["DRI"] = _clean_stat(cols[12].get_text(strip=True)) if len(cols) > 12 else 0
        player["DEF"] = _clean_stat(cols[13].get_text(strip=True)) if len(cols) > 13 else 0
        player["PHY"] = _clean_stat(cols[14].get_text(strip=True)) if len(cols) > 14 else 0

        # td[17] — Height + AcceleRATE
        height_text = cols[17].get_text(strip=True) if len(cols) > 17 else ""
        player["Height"] = height_text
        # Extract AcceleRATE if present (e.g. "Explosive", "Lengthy", "Controlled")
        acc_rate = ""
        for rate_type in ("Explosive", "Lengthy", "Controlled"):
            if rate_type in height_text:
                acc_rate = rate_type
                break
        player["AcceleRATE"] = acc_rate

        # Build Futwiz link
        player["Futwiz Link"] = build_futwiz_link(slug, def_id)
        player["ID"] = def_id

        players.append(player)

    return players


def get_total_pages(session: requests.Session) -> int:
    """Get the total number of player pages from Futbin."""
    resp = session.get(f"{BASE_URL}?page=1", headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Scan ALL links with page= parameter — pagination links are not
    # always inside a <nav> or <ul class="pagination">.
    max_page = 1
    for link in soup.find_all("a", href=True):
        m = re.search(r"page=(\d+)", link["href"])
        if m:
            max_page = max(max_page, int(m.group(1)))

    return max_page


# Columns we actually scrape from Futbin listing pages.
# Everything else (detailed stats like Acceleration, Finishing, etc.)
# is not available and defaults to "0".
_SCRAPED_FIELDS = {
    "Name", "Version", "Club", "League", "Nationality", "Price",
    "Position", "ID", "Overall Rating", "Futwiz Link",
    "PAC", "SHO", "PAS", "DRI", "DEF", "PHY",
    "AcceleRATE", "Foot", "Skill Moves", "Weak Foot", "Height",
}


def player_to_csv_row(player: dict) -> list[str]:
    """Convert a scraped player dict to a full 69-column CSV row."""
    row = []
    for col in CSV_COLUMNS:
        if col in _SCRAPED_FIELDS:
            row.append(str(player.get(col, "")))
        else:
            # Detailed stats not available from listing — fill with 0
            row.append("0")
    return row


def scrape_all_pages(
    max_pages: int | None = None,
    delay: float = 1.5,
    output_path: str | None = None,
) -> pathlib.Path:
    """
    Scrape Futbin FC26 players and write CSV.

    Args:
        max_pages: Max pages to scrape. None = all pages.
        delay: Seconds between requests (be polite to Futbin).
        output_path: Path for output CSV. Defaults to data/csv/fc26_players.csv.

    Returns:
        Path to the generated CSV file.
    """
    if output_path is None:
        output_path = str(
            pathlib.Path(__file__).parent.parent / "csv" / "fc26_players.csv"
        )

    session = requests.Session()
    total_pages = get_total_pages(session)
    pages_to_scrape = min(total_pages, max_pages) if max_pages else total_pages

    print(f"Futbin FC26: {total_pages} pages total, scraping {pages_to_scrape}")

    all_players = []
    for page in range(1, pages_to_scrape + 1):
        try:
            players = scrape_page(page, session)
            all_players.extend(players)
            print(f"  Page {page}/{pages_to_scrape}: {len(players)} players", flush=True)
        except requests.RequestException as e:
            print(f"  Page {page} failed: {e}", flush=True)
            # Retry once after a longer pause
            time.sleep(5)
            try:
                players = scrape_page(page, session)
                all_players.extend(players)
                print(f"  Page {page} retry OK: {len(players)} players", flush=True)
            except requests.RequestException:
                print(f"  Page {page} retry failed, skipping", flush=True)

        if page < pages_to_scrape:
            time.sleep(delay)

    # Write CSV
    out = pathlib.Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(CSV_COLUMNS)  # header
        for player in all_players:
            writer.writerow(player_to_csv_row(player))

    print(f"\nDone! {len(all_players)} players saved to {out}")
    return out


def main():
    parser = argparse.ArgumentParser(description="Scrape FC26 players from Futbin")
    parser.add_argument(
        "--pages", type=int, default=None,
        help="Max pages to scrape (default: all)",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output CSV path (default: data/csv/fc26_players.csv)",
    )
    parser.add_argument(
        "--delay", type=float, default=1.5,
        help="Delay between requests in seconds (default: 1.5)",
    )
    args = parser.parse_args()
    scrape_all_pages(
        max_pages=args.pages,
        delay=args.delay,
        output_path=args.output,
    )


if __name__ == "__main__":
    main()
