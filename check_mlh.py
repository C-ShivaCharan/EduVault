import requests

url = "https://mlh.io/seasons/2026/events"
headers = {'User-Agent': 'Mozilla/5.0'}
try:
    r = requests.get(url, headers=headers)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        print("Page exists")
        # specific check if it's a soft 404 or redirect
        if "2026" in r.url:
            print("Confirmed 2026")
        else:
            print(f"Redirected to {r.url}")
except Exception as e:
    print(f"Error: {e}")
