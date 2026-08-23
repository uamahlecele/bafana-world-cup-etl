import requests

# Initial call without this rejected my request because it wasn't coming from a browser, this helps with that.
headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

}

response = requests.get(
    "https://api.fifa.com/api/v3/competitions/teams/285023",
    headers=headers
)

print("This is the result:\n")
print("STATUS CODE:",response.status_code)

print(response.text)