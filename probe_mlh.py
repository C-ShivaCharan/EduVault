import requests
import re

url = "https://mlh.io/seasons/2026/events"
headers = {'User-Agent': 'Mozilla/5.0'}
try:
    r = requests.get(url, headers=headers)
    html = r.text
    # Find patterns looking like event cards
    # Look for class names
    print("Classes found near 'event':")
    print(re.findall(r'class="[^"]*event[^"]*"', html)[:10])
    
    # improved probe: look for an event link
    print("\nPotential Event Links:")
    # MLH event links usually go to the event site or a specific MLH page
    links = re.findall(r'<a[^>]*href="([^"]*)"[^>]*title="([^"]*)"', html)
    print(links[:5])
    
    # Dump a small chunk
    start = html.find('<div class="event-wrapper"')
    if start == -1:
        start = html.find('event')
    print(f"\nSnippet:\n{html[start:start+1000]}")

except Exception as e:
    print(e)
