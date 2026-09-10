import requests

# Returns results of some of the matches of the 2026 tournament
MATCHES_2026_WC = "https://api.fifa.com/api/v3/calendar/matches"
TEAMS_2026_WC = "https://api.fifa.com/api/v3/competitions/teams/285023"

# Initial call without this rejected my request because it wasn't coming from a browser, this helps with that.
headers = { "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

# Query params for matches, kept separate from the URL so we can add
# token/hash to them on later pages
match_params = {
    "idCompetition": 17,
    "idSeason": 285023
}

#API CALLS
teams_2026 = requests.get(TEAMS_2026_WC, headers=headers)

#STORES RELEVANT COLUMNS FOR SUBSEQUENT DB 
clean_matches = []
clean_teams = []

# Convert the teams response into a python dictionary
teams_2026 = teams_2026.json()
all_teams = teams_2026["Results"]

# --- PAGINATION LOOP FOR MATCHES ---
# The matches endpoint only returns one "page" of results at a time.
# If ContinuationToken is not null, there's more data waiting, so we
# keep requesting pages until FIFA tells us there's nothing left.
all_match_results = []
continuation_token = None
continuation_hash = None
page_number = 1

# SAFETY CAP: without this, a bug in the pagination logic (token not
# actually advancing) causes an infinite loop, as we just saw happen.
# 30 pages is way more than the ~104 matches / 50 per page (~3 pages)
# we'd expect for a full tournament, so this is just a guard rail.
MAX_PAGES = 30

while True:
    if page_number > MAX_PAGES:
        print(f"Hit safety cap of {MAX_PAGES} pages — pagination isn't advancing correctly. Stopping to investigate.")
        break

    # On the first loop these are still None, so params stays as the base query.
    # On later loops we add the token/hash we got back from the previous response.
    if continuation_token:
        match_params["token"] = continuation_token
        match_params["hash"] = continuation_hash

    tournament_matches = requests.get(MATCHES_2026_WC, headers=headers, params=match_params)

    # DEBUG: print the exact URL that was actually sent, so we can compare
    # page 1's URL against page 2's URL and confirm the token/hash are
    # really changing between requests (not just sitting there unused).
    print(f"Page {page_number} URL: {tournament_matches.url}")
    print(f"Status code: {tournament_matches.status_code}")

    matches = tournament_matches.json()

    page_results = matches["Results"]
    print(f"Page {page_number}: got {len(page_results)} matches")

    all_match_results.extend(page_results)

    continuation_token = matches["ContinuationToken"]
    continuation_hash = matches["ContinuationHash"]

    # DEBUG: show the new token so we can see whether it's actually
    # different from the previous page's token, or suspiciously identical.
    print(f"New continuation_token (first 40 chars): {str(continuation_token)[:40]}")
    print("")

    if not continuation_token:
        break

    page_number += 1

print(f"\nTotal matches collected across all pages: {len(all_match_results)}\n")

for match in all_match_results:
    clean_matches.append({
        "id_match": match["IdMatch"],
        "date": match["Date"],
        "stage": match["StageName"][0]["Description"],
        "group_name": match["GroupName"][0]["Description"] if match["GroupName"] else None,
        "home_team_id": match["Home"]["IdTeam"],
        "home_team_name": match["Home"]["TeamName"][0]["Description"],
        "home_score": match["Home"]["Score"],
        "away_team_id": match["Away"]["IdTeam"],
        "away_team_name": match["Away"]["TeamName"][0]["Description"],
        "away_score": match["Away"]["Score"],
        "winner_id": match["Winner"],
        "stadium": match["Stadium"]["Name"][0]["Description"],
        "attendance": match["Attendance"],
    })

for m in clean_matches:
    print(m)