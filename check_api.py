import requests

urls = [
    "https://www.hackalist.org/api/1.0/2026/02.json",
    "https://www.hackalist.org/api/1.0/2025/02.json",
    "https://www.hackalist.org/api/1.0/2025/01.json"
]

for url in urls:
    try:
        r = requests.head(url)
        print(f"{url}: {r.status_code}")
    except Exception as e:
        print(f"{url}: Error {e}")
