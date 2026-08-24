import requests

# Initial call without this rejected my request because it wasn't coming from a browser, this helps with that.
headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

}

response = requests.get(
    'https://api.fifa.com/api/v3/competitions/teams/285023',
    headers=headers
)

# Convert the response into a python dictionary
response = response.json()

# print(response)

teams = response["Results"]
print(teams)
print("")
print("")
print("first team\n\n", teams[0])
print("Second team\n\n",teams[1])

print(f"Number of teams: {len(teams)}")

for team_name in teams:
    for key,value in team_name.items():
        if key == 'ShortClubName' or key =="IdTeam":
            print(value)
        else:
            continue

# print("This is the result:\n")
# print("STATUS CODE:",response.status_code)

# print(response.json())