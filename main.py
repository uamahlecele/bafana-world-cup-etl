import requests

# Returns results of some of the matches of the 2026 tournament

MATCHES_2026_WC = "https://api.fifa.com/api/v3/calendar/matches?idCompetition=17&idSeason=285023"
TEAMS_2026_WC = "https://api.fifa.com/api/v3/competitions/teams/285023"

# Initial call without this rejected my request because it wasn't coming from a browser, this helps with that.
headers = { "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

#API CALLS
teams_2026 = requests.get(TEAMS_2026_WC, headers=headers)
tournament_matches = requests.get(MATCHES_2026_WC, headers=headers)

#STORES RELEVANT COLUMNS FOR SUBSEQUENT DB 
clean_matches = []
clean_teams = []

# Convert the response into a python dictionary
teams_2026 = teams_2026.json()
matches = tournament_matches.json()

match_results = matches["Results"]
all_teams = teams_2026["Results"]
# print(response)

# print(match_results)

for match in match_results:
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

for m in clean_matches[:5]:
    print(m)

    
# print(teams)
# print("")
# print("")
# print("first team\n\n", teams[0])
# print("Second team\n\n",teams[1])

# print(f"Number of teams: {len(teams)}")




# for team_name in teams:
#     for key,value in team_name.items():
#         if key == 'ShortClubName' or key =="IdTeam":
#             print(value)
#         else:
#             continue

# print("This is the result:\n")
# print("STATUS CODE:",response.status_code)

# print(response.json())