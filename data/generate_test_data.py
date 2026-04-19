"""Generate a synthetic FC26 players CSV for testing the SBC solver."""

import csv
import pathlib

# 70-column template — must match CSV_COLUMNS in futbin_scraper.py exactly.
HEADER = [
    "Name", "Version", "Club", "League", "Nationality", "Alt Pos.", "Skill Moves",
    "Weak Foot", "Foot", "Att W/R", "Def W/R", "Age", "Height", "Weight",
    "Body Type", "Added", "Price", "Position", "ID", "Overall Rating",
    "Futwiz Link",
    "PAC", "AcceleRATE", "Acceleration", "Sprint Speed",
    "SHO", "Positioning", "Finishing", "Shot Power", "Long Shots", "Volleys",
    "Penalties",
    "PAS", "Vision", "Crossing", "FK. Acc.", "Short Pass", "Long Pass", "Curve",
    "DRI", "Agility", "Balance", "Reactions", "Ball Control", "Dribbling",
    "Composure",
    "DEF", "Interceptions", "Heading Acc.", "Def. Awareness", "Stand Tackle",
    "Slide Tackle",
    "PHY", "Jumping", "Stamina", "Strength", "Aggression",
    "PlayStyles+", "PlayStyles",
    "DIV", "GK. Diving", "REF", "GK. Reflexes", "HAN", "GK. Handling",
    "SPD", "KIC", "GK. Kicking", "POS", "GK. Pos",
]

# Each tuple: (Name, Version, Club, League, Nationality, Alt Pos, Price, Position, ID, Rating, PAC, SHO, PAS, DRI, DEF, PHY)
# Stats are simplified — only the 6 composite stats matter for the solver check.
PLAYERS = [
    # GK (5)
    ("Alisson", "Rare", "Liverpool", "Premier League", "Brazil", "", 85000, "GK", "200001", 87, 48, 0, 0, 0, 0, 0),
    ("Courtois", "Rare", "Real Madrid", "LaLiga", "Belgium", "", 120000, "GK", "200002", 90, 50, 0, 0, 0, 0, 0),
    ("M. ter Stegen", "Rare", "FC Barcelona", "LaLiga", "Germany", "", 92000, "GK", "200003", 88, 45, 0, 0, 0, 0, 0),
    ("Donnarumma", "Rare", "Paris Saint-Germain", "Ligue 1", "Italy", "", 78000, "GK", "200004", 87, 47, 0, 0, 0, 0, 0),
    ("Ederson", "Rare", "Manchester City", "Premier League", "Brazil", "", 82000, "GK", "200005", 87, 52, 0, 0, 0, 0, 0),
    # CB (8)
    ("Van Dijk", "Rare", "Liverpool", "Premier League", "Netherlands", "", 110000, "CB", "200006", 89, 72, 55, 70, 68, 90, 86),
    ("Rúben Dias", "Rare", "Manchester City", "Premier League", "Portugal", "", 88000, "CB", "200007", 88, 68, 48, 65, 62, 89, 84),
    ("Marquinhos", "Rare", "Paris Saint-Germain", "Ligue 1", "Brazil", "", 76000, "CB", "200008", 87, 70, 52, 68, 66, 88, 82),
    ("Militão", "Rare", "Real Madrid", "LaLiga", "Brazil", "", 65000, "CB", "200009", 86, 74, 50, 58, 60, 86, 84),
    ("Araújo", "Rare", "FC Barcelona", "LaLiga", "Uruguay", "", 62000, "CB", "200010", 86, 72, 46, 55, 58, 87, 83),
    ("Bastoni", "Rare", "Inter", "Serie A", "Italy", "", 58000, "CB", "200011", 86, 65, 48, 72, 64, 86, 80),
    ("Saliba", "Rare", "Arsenal", "Premier League", "France", "", 64000, "CB", "200012", 86, 70, 44, 58, 60, 88, 82),
    ("De Ligt", "Rare", "Manchester United", "Premier League", "Netherlands", "", 55000, "CB", "200013", 85, 64, 50, 62, 60, 85, 82),
    # LB (4)
    ("Robertson", "Rare", "Liverpool", "Premier League", "Scotland", "", 42000, "LB", "200014", 85, 80, 60, 82, 78, 76, 74),
    ("Davies", "Rare", "Bayern München", "Bundesliga", "Canada", "", 38000, "LB", "200015", 84, 88, 56, 72, 76, 72, 72),
    ("Balde", "Rare", "Inter", "Serie A", "Italy", "", 32000, "LB", "200016", 83, 86, 54, 70, 80, 70, 68),
    ("Theo Hernández", "Rare", "AC Milan", "Serie A", "France", "", 52000, "LB", "200017", 86, 86, 62, 70, 76, 72, 78),
    # RB (4)
    ("Alexander-Arnold", "Rare", "Liverpool", "Premier League", "England", "", 68000, "RB", "200018", 87, 76, 62, 90, 78, 70, 68),
    ("Hakimi", "Rare", "Paris Saint-Germain", "Ligue 1", "Morocco", "", 48000, "RB", "200019", 84, 82, 58, 72, 76, 72, 70),
    ("Cancelo", "Rare", "FC Barcelona", "LaLiga", "Portugal", "", 45000, "RB", "200020", 84, 78, 64, 80, 82, 68, 72),
    ("Carvajal", "Rare", "Real Madrid", "LaLiga", "Spain", "", 52000, "RB", "200021", 86, 76, 56, 74, 72, 80, 76),
    # CDM (4)
    ("Rodri", "Rare", "Manchester City", "Premier League", "Spain", "", 180000, "CDM", "200022", 91, 62, 64, 82, 78, 82, 80),
    ("Casemiro", "Rare", "Manchester United", "Premier League", "Brazil", "", 42000, "CDM", "200023", 85, 58, 56, 68, 64, 84, 82),
    ("Tchouaméni", "Rare", "Real Madrid", "LaLiga", "France", "", 68000, "CDM", "200024", 86, 64, 58, 72, 68, 84, 80),
    ("Xhaka", "Rare", "Bayer Leverkusen", "Bundesliga", "Switzerland", "", 35000, "CDM", "200025", 84, 56, 62, 78, 66, 80, 78),
    # CM (9)
    ("De Bruyne", "Rare", "Manchester City", "Premier League", "Belgium", "", 220000, "CM", "200026", 91, 72, 86, 92, 86, 58, 74),
    ("Modrić", "Rare", "Real Madrid", "LaLiga", "Croatia", "", 58000, "CM", "200027", 87, 72, 76, 88, 88, 64, 64),
    ("Valverde", "Rare", "Real Madrid", "LaLiga", "Uruguay", "", 95000, "CM", "200028", 88, 84, 72, 76, 78, 72, 82),
    ("Pedri", "Rare", "FC Barcelona", "LaLiga", "Spain", "", 82000, "CM", "200029", 87, 76, 68, 86, 90, 64, 68),
    ("Bellingham", "Rare", "Real Madrid", "LaLiga", "England", "", 160000, "CM", "200030", 90, 78, 80, 78, 82, 70, 78),
    ("Bruno Fernandes", "Rare", "Manchester United", "Premier League", "Portugal", "", 78000, "CM", "200031", 88, 68, 82, 88, 82, 58, 72),
    ("Bernardo Silva", "Rare", "Manchester City", "Premier League", "Portugal", "", 72000, "CM", "200032", 87, 72, 70, 84, 90, 58, 64),
    ("Ødegaard", "Rare", "Arsenal", "Premier League", "Norway", "", 68000, "CM", "200033", 87, 70, 74, 88, 88, 52, 62),
    ("Frenkie de Jong", "Rare", "FC Barcelona", "LaLiga", "Netherlands", "", 62000, "CM", "200034", 86, 72, 62, 80, 88, 66, 72),
    # CAM (3)
    ("Wirtz", "Rare", "Bayer Leverkusen", "Bundesliga", "Germany", "", 78000, "CAM", "200035", 86, 76, 78, 82, 88, 42, 58),
    ("Foden", "Rare", "Manchester City", "Premier League", "England", "", 82000, "CAM", "200036", 87, 78, 78, 82, 88, 44, 58),
    ("Musiala", "Rare", "Bayern München", "Bundesliga", "Germany", "", 85000, "CAM", "200037", 86, 76, 74, 78, 90, 38, 56),
    # LM (5)
    ("Leão", "Rare", "AC Milan", "Serie A", "Portugal", "", 62000, "LM", "200038", 86, 88, 72, 72, 84, 38, 68),
    ("Nico Williams", "Rare", "Athletic Club", "LaLiga", "Spain", "", 54000, "LM", "200039", 85, 88, 68, 74, 86, 42, 66),
    ("Lookman", "Rare", "Atalanta", "Serie A", "Nigeria", "", 38000, "LM", "200040", 84, 84, 74, 70, 84, 40, 64),
    ("Mitoma", "Rare", "Brighton", "Premier League", "Japan", "", 32000, "LM", "200041", 83, 84, 66, 72, 86, 38, 60),
    ("Kvaratskhelia", "Rare", "Paris Saint-Germain", "Ligue 1", "Georgia", "", 58000, "LM", "200042", 85, 82, 72, 76, 86, 40, 64),
    # RM (3)
    ("Salah", "Rare", "Liverpool", "Premier League", "Egypt", "", 95000, "RM", "200043", 87, 82, 86, 78, 84, 42, 68),
    ("Saka", "Rare", "Arsenal", "Premier League", "England", "", 72000, "RM", "200044", 86, 82, 76, 80, 86, 48, 64),
    ("Coman", "Rare", "Bayern München", "Bundesliga", "France", "", 38000, "RM", "200045", 84, 84, 68, 74, 86, 38, 62),
    # LW (4)
    ("Vinícius Jr", "Rare", "Real Madrid", "LaLiga", "Brazil", "", 200000, "LW", "200046", 90, 90, 78, 76, 92, 36, 62),
    ("Son", "Rare", "Tottenham", "Premier League", "South Korea", "", 62000, "LW", "200047", 86, 82, 84, 76, 82, 40, 62),
    ("Dembélé", "Rare", "Paris Saint-Germain", "Ligue 1", "France", "", 85000, "LW", "200048", 87, 88, 76, 78, 90, 36, 58),
    ("Rodrygo", "Rare", "Real Madrid", "LaLiga", "Brazil", "", 68000, "LW", "200049", 86, 84, 76, 76, 86, 40, 60),
    # CF (2)
    ("Griezmann", "Rare", "Atlético Madrid", "LaLiga", "France", "", 48000, "CF", "200050", 85, 72, 80, 82, 82, 52, 68),
    ("Diogo Jota", "Rare", "Liverpool", "Premier League", "Portugal", "", 42000, "CF", "200051", 84, 74, 82, 68, 78, 44, 72),
    # ST (8)
    ("Haaland", "Rare", "Manchester City", "Premier League", "Norway", "", 250000, "ST", "200052", 91, 88, 92, 66, 76, 44, 88),
    ("Kane", "Rare", "Bayern München", "Bundesliga", "England", "", 120000, "ST", "200053", 90, 70, 90, 82, 86, 46, 82),
    ("Lewandowski", "Rare", "FC Barcelona", "LaLiga", "Poland", "", 62000, "ST", "200054", 86, 68, 86, 76, 82, 44, 78),
    ("Lautaro", "Rare", "Inter", "Serie A", "Argentina", "", 72000, "ST", "200055", 87, 78, 84, 68, 80, 48, 76),
    ("Julián Álvarez", "Rare", "Atlético Madrid", "LaLiga", "Argentina", "", 65000, "ST", "200056", 86, 78, 82, 66, 82, 44, 74),
    ("Vlahović", "Rare", "Juventus", "Serie A", "Serbia", "", 40000, "ST", "200057", 84, 74, 82, 58, 78, 40, 76),
    ("Mbappé", "Rare", "Real Madrid", "LaLiga", "France", "", 300000, "ST", "200058", 91, 90, 88, 80, 88, 38, 72),
    ("Osimhen", "Rare", "Galatasaray", "Süper Lig", "Nigeria", "", 48000, "ST", "200059", 85, 84, 82, 54, 74, 38, 80),
    # Special IF/TOTW versions (3) — these count as Rare too
    ("Haaland", "IF", "Manchester City", "Premier League", "Norway", "", 650000, "ST", "200060", 93, 90, 94, 68, 78, 46, 90),
    ("Mbappé", "TOTW", "Real Madrid", "LaLiga", "France", "", 800000, "ST", "200061", 94, 92, 90, 82, 90, 40, 74),
    ("Bellingham", "TOTW", "Real Madrid", "LaLiga", "England", "", 350000, "CM", "200062", 92, 80, 82, 80, 84, 72, 80),
]


def _make_row(p):
    """Build a 70-column row from a player tuple."""
    name, version, club, league, nat, alt_pos, price, pos, pid, rating = p[:10]
    pac, sho, pas, dri, phy = p[10], p[11], p[12], p[13], p[15]

    # Composite DEF — derive rough individual stats
    composite_def = p[14]

    # Generate plausible sub-stats from composites
    def stat_range(val, spread=4):
        return max(0, val - spread), min(99, val + spread)

    # Common pos stats derived from composites
    acc = min(99, pac + 2)
    sprint = max(0, pac - 2)
    positioning = min(99, sho + 2)
    finishing = max(0, sho - 2)
    shot_power = min(99, sho + 4)
    long_shots = max(0, sho - 3)
    volleys = max(0, sho - 5)
    penalties = max(0, sho - 2)
    vision = min(99, pas + 2)
    crossing = max(0, pas - 4)
    fk_acc = max(0, pas - 6)
    short_pass = min(99, pas + 2)
    long_pass = max(0, pas - 2)
    curve = max(0, pas - 4)
    agility = min(99, dri + 2)
    balance = min(99, dri + 4)
    reactions = min(99, rating - 2)
    ball_control = min(99, dri + 2)
    dribbling = min(99, dri + 1)
    composure = min(99, rating)
    interceptions = max(0, composite_def + 2)
    heading = max(0, composite_def - 2)
    def_awareness = min(99, composite_def + 3)
    stand_tackle = min(99, composite_def + 1)
    slide_tackle = max(0, composite_def - 1)
    jumping = min(99, phy + 4)
    stamina = min(99, phy + 2)
    strength = min(99, phy + 2)
    aggression = max(0, phy - 2)

    # GK stats — only for GK position
    is_gk = pos == "GK"
    if is_gk:
        gk_base = rating - 5
        div = gk_base + 3
        ref = gk_base + 5
        han = gk_base
        kic = gk_base - 10
        gk_pos = gk_base + 2
        spd = gk_base - 8
    else:
        div = ref = han = kic = gk_pos = spd = 0

    # PlayStyles — leave empty
    playstyles_plus = ""
    playstyles = ""

    # Alt Pos
    alt = alt_pos

    # Skill Moves / Weak Foot — plausible values based on rating
    sm = 4 if rating >= 86 else 3
    wf = 4 if rating >= 87 else 3
    foot = "Right"
    att_wr = "High" if rating >= 87 else "Medium"
    def_wr = "Medium"
    age = 26
    height = "182 cm"
    weight = "76 kg"
    body_type = "Normal"
    added = "2025-09-12"
    futwiz = f"https://www.futwiz.com/en/fc26/player/{name.lower().replace(' ', '-')}/{pid}"
    accelerate = "Controlled" if pac < 82 else "Explosive"

    return [
        name, version, club, league, nat, alt, str(sm), str(wf), foot, att_wr,
        def_wr, str(age), height, weight, body_type, added, str(price), pos, pid,
        str(rating), futwiz,
        # Common pos stats (38 cols)
        str(pac), accelerate, str(acc), str(sprint),
        str(sho), str(positioning), str(finishing), str(shot_power), str(long_shots),
        str(volleys), str(penalties),
        str(pas), str(vision), str(crossing), str(fk_acc), str(short_pass),
        str(long_pass), str(curve),
        str(dri), str(agility), str(balance), str(reactions), str(ball_control),
        str(dribbling), str(composure),
        str(composite_def), str(interceptions), str(heading), str(def_awareness),
        str(stand_tackle), str(slide_tackle),
        str(phy), str(jumping), str(stamina), str(strength), str(aggression),
        playstyles_plus, playstyles,
        # GK stats (11 cols)
        str(div - 30 if is_gk else 0), str(div), str(ref - 30 if is_gk else 0),
        str(ref), str(han - 30 if is_gk else 0), str(han),
        str(spd), str(kic - 30 if is_gk else 0), str(kic),
        str(gk_pos - 30 if is_gk else 0), str(gk_pos),
    ]


def main():
    out = pathlib.Path(__file__).parent / "csv" / "fc26_players.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(HEADER)
        for p in PLAYERS:
            writer.writerow(_make_row(p))
    print(f"Generated {len(PLAYERS)} players → {out}")


if __name__ == "__main__":
    main()
