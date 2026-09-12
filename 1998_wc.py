"""
FIFA World Cup 1998 ETL Pipeline
Standalone script — reads the 1998 teams.csv and results.csv from the
stiles/world-cup repo, cleans the data, and loads it into the SAME
SQLite database as the 2026 pipeline, tagged with year=2010.
"""

import csv
import sqlite3

# --- CONFIG ---
TEAMS_CSV_PATH = "1998/teams.csv"
RESULTS_CSV_PATH = "1998/results.csv"
DB_NAME = "bafana_bafana_wc.db"
YEAR = 1998


# EXTRACT — reading raw data from local CSV files

def extract_teams():
    """Read the 2010 teams CSV, return a list of raw row dicts."""
    with open(TEAMS_CSV_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


def extract_matches():
    """Read the 2010 results CSV, return a list of raw row dicts."""
    with open(RESULTS_CSV_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


# TRANSFORM — cleaning and reshaping raw CSV rows into our standard schema

def transform_teams(raw_teams):
    """
    Map 2010 CSV columns onto the same clean shape used by the 2026 pipeline:
    id_team, name, confederation, abbreviation, year

    CSV columns available: id_team, confederation, team_name, short_name,
    abbreviation, country_code, foundation_year, flag_url
    """
    clean_teams = []
    for team in raw_teams:
        clean_teams.append({
            "id_team": int(team["id_team"]),
            "name": team["short_name"],
            "confederation": team["confederation"],
            "abbreviation": team["abbreviation"],
            "year": YEAR,
        })
    return clean_teams


def build_team_lookup(raw_teams):
    """Build abbreviation -> id_team map, e.g. {"RSA": 43883, "MEX": 43911}."""
    return {team["abbreviation"]: int(team["id_team"]) for team in raw_teams}


def transform_matches(raw_matches, team_lookup):
    """
    Map 2010 CSV columns onto the same clean shape used by the 2026 pipeline:
    id_match, date, stage, group_name, home_team_id, away_team_id,
    home_score, away_score, winner_id, stadium, attendance, year

    NOTE: 2010's CSV stores home/away/winner as team ABBREVIATIONS
    (e.g. "RSA"), not numeric IDs like the FIFA API used for 2026.
    We resolve them to numeric id_team values via team_lookup so 2010
    rows join cleanly with 2026 rows. Raises ValueError listing any
    abbreviations that fail to resolve.
    """
    clean_matches = []
    unmatched = set()

    def resolve(abbr, id_match):
        if abbr in team_lookup:
            return team_lookup[abbr]
        unmatched.add((abbr, id_match))
        return None

    for match in raw_matches:
        id_match = match["id_match"]
        home_id = resolve(match["home_team"], id_match)
        away_id = resolve(match["away_team"], id_match)
        winner_abbr = match["winner"].strip()
        winner_id = resolve(winner_abbr, id_match) if winner_abbr else None

        clean_matches.append({
            "id_match": int(id_match),
            "date": match["date_utc"],
            "stage": match["stage"],
            "group_name": match["group"] if match["group"] else None,
            "home_team_id": home_id,
            "away_team_id": away_id,
            "home_score": int(match["home_score"]) if match["home_score"] else None,
            "away_score": int(match["away_score"]) if match["away_score"] else None,
            "winner_id": winner_id,
            "stadium": match["stadium"],
            "attendance": int(match["attendance"]) if match["attendance"] else None,
            "year": YEAR,
        })

    if unmatched:
        details = ", ".join(f"{abbr} (match {mid})" for abbr, mid in sorted(unmatched))
        raise ValueError(f"Unmatched team abbreviations in results.csv: {details}")

    return clean_matches


# LOAD — writing clean data into the shared SQLite database

def load_to_sqlite(clean_teams, clean_matches, db_name=DB_NAME):
    """
    Insert into the same teams/matches tables the 2026 pipeline created.
    Uses CREATE TABLE IF NOT EXISTS so this never wipes out other years,
    and INSERT OR REPLACE so re-running this script is safe.
    """
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS teams (
        id_team INTEGER,
        name TEXT,
        confederation TEXT,
        abbreviation TEXT,
        year INTEGER,
        PRIMARY KEY (id_team, year)
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS matches (
        id_match INTEGER PRIMARY KEY,
        date TEXT,
        stage TEXT,
        group_name TEXT,
        home_team_id INTEGER,
        away_team_id INTEGER,
        home_score INTEGER,
        away_score INTEGER,
        winner_id INTEGER,
        stadium TEXT,
        attendance INTEGER,
        year INTEGER
    )''')

    for team in clean_teams:
        cursor.execute('''INSERT OR REPLACE INTO teams VALUES (?, ?, ?, ?, ?)''',
                       (team["id_team"], team["name"], team["confederation"],
                        team["abbreviation"], team["year"]))

    for match in clean_matches:
        cursor.execute('''INSERT OR REPLACE INTO matches VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                       (match["id_match"], match["date"], match["stage"], match["group_name"],
                        match["home_team_id"], match["away_team_id"], match["home_score"],
                        match["away_score"], match["winner_id"], match["stadium"],
                        match["attendance"], match["year"]))

    connection.commit()
    connection.close()
    print(f"1998 data loaded into SQLite successfully! Database file: {db_name}")


# ORCHESTRATION

def main():
    raw_teams = extract_teams()
    raw_matches = extract_matches()

    clean_teams = transform_teams(raw_teams)
    team_lookup = build_team_lookup(raw_teams)
    clean_matches = transform_matches(raw_matches, team_lookup)

    load_to_sqlite(clean_teams, clean_matches)


if __name__ == "__main__":
    main()