import requests
import sqlite3
from collections import Counter

# --- CONFIG ---
MATCHES_2026_WC = "https://api.fifa.com/api/v3/calendar/matches"
TEAMS_2026_WC = "https://api.fifa.com/api/v3/competitions/teams/285023"

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

MAX_PAGES = 30  # safety cap in case pagination doesn't advance correctly
DB_NAME = "bafana_bafana_wc.db"

# EXTRACT — pulling raw data from the FIFA API

def extract_teams():
    """Call the FIFA teams API, return raw team results (unprocessed JSON)."""
    response = requests.get(TEAMS_2026_WC, headers=headers)
    return response.json()["Results"]


def extract_matches():
    """
    Call the FIFA matches API, handling pagination via token/hash.
    Returns all raw match results collected across every page.
    """
    match_params = {
        "idCompetition": 17,
        "idSeason": 285023
    }

    all_match_results = []
    continuation_token = None
    continuation_hash = None
    page_number = 1

    while True:
        if page_number > MAX_PAGES:
            print(f"Hit safety cap of {MAX_PAGES} pages — stopping.")
            break

        if continuation_token:
            match_params["token"] = continuation_token
            match_params["hash"] = continuation_hash

        response = requests.get(MATCHES_2026_WC, headers=headers, params=match_params)
        data = response.json()

        page_results = data["Results"]
        print(f"Page {page_number}: got {len(page_results)} matches")
        all_match_results.extend(page_results)

        continuation_token = data["ContinuationToken"]
        continuation_hash = data["ContinuationHash"]

        if not continuation_token:
            break
        page_number += 1

    print(f"Total raw matches collected: {len(all_match_results)}\n")
    return all_match_results

# TRANSFORM — cleaning and reshaping raw data

def deduplicate_matches(raw_matches):
    """Remove duplicate match entries by IdMatch (pagination can overlap)."""
    ids = [m["IdMatch"] for m in raw_matches]
    if len(ids) != len(set(ids)):
        dupes = [id for id, count in Counter(ids).items() if count > 1]
        print(f"WARNING: {len(dupes)} duplicate match IDs found and removed")

    seen_ids = set()
    deduped = []
    for match in raw_matches:
        if match["IdMatch"] not in seen_ids:
            seen_ids.add(match["IdMatch"])
            deduped.append(match)

    print(f"After deduplication: {len(deduped)} matches\n")
    return deduped


def transform_teams(raw_teams):
    """Flatten raw team JSON into clean dicts with just the fields we need."""
    clean_teams = []
    for team in raw_teams:
        clean_teams.append({
            "id_team": team["IdTeam"],
            "name": team["ShortClubName"],
            "confederation": team["IdConfederation"],
            "abbreviation": team["Abbreviation"],
        })
    return clean_teams


def transform_matches(raw_matches):
    """Flatten raw match JSON into clean dicts with just the fields we need."""
    clean_matches = []
    for match in raw_matches:
        clean_matches.append({
            "id_match": match["IdMatch"],
            "date": match["Date"],
            "stage": match["StageName"][0]["Description"],
            "group_name": match["GroupName"][0]["Description"] if match["GroupName"] else None,
            "home_team_id": match["Home"]["IdTeam"],
            "home_score": match["Home"]["Score"],
            "away_team_id": match["Away"]["IdTeam"],
            "away_score": match["Away"]["Score"],
            "winner_id": match["Winner"],
            "stadium": match["Stadium"]["Name"][0]["Description"],
            "attendance": match["Attendance"],
        })
    return clean_matches


# LOAD — writing clean data into SQLite

def load_to_sqlite(clean_teams, clean_matches, db_name=DB_NAME):
    """Create the teams/matches tables and insert the cleaned data."""
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()

    # Drop tables first so the script can be safely re-run
    cursor.execute('DROP TABLE IF EXISTS teams')
    cursor.execute('DROP TABLE IF EXISTS matches')

    cursor.execute('''CREATE TABLE teams (
        id_team TEXT PRIMARY KEY,
        name TEXT,
        confederation TEXT,
        abbreviation TEXT
    )''')

    cursor.execute('''CREATE TABLE matches (
        id_match TEXT PRIMARY KEY,
        date TEXT,
        stage TEXT,
        group_name TEXT,
        home_team_id TEXT,
        away_team_id TEXT,
        home_score INTEGER,
        away_score INTEGER,
        winner_id TEXT,
        stadium TEXT,
        attendance INTEGER
    )''')

    for team in clean_teams:
        cursor.execute('''INSERT INTO teams VALUES (?, ?, ?, ?)''',
                       (team["id_team"], team["name"], team["confederation"], team["abbreviation"]))

    for match in clean_matches:
        cursor.execute('''INSERT INTO matches VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                       (match["id_match"], match["date"], match["stage"], match["group_name"],
                        match["home_team_id"], match["away_team_id"], match["home_score"],
                        match["away_score"], match["winner_id"], match["stadium"], match["attendance"]))

    connection.commit()
    connection.close()
    print(f"Data loaded into SQLite successfully! Database file: {db_name}")


# ORCHESTRATION — runs Extract -> Transform -> Load in order

def main():
    # EXTRACT
    raw_teams = extract_teams()
    raw_matches = extract_matches()

    # TRANSFORM
    deduped_matches = deduplicate_matches(raw_matches)
    clean_teams = transform_teams(raw_teams)
    clean_matches = transform_matches(deduped_matches)

    # LOAD
    load_to_sqlite(clean_teams, clean_matches)


if __name__ == "__main__":
    main()