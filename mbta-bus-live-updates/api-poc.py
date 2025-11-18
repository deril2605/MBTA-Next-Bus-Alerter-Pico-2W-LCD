import requests
import datetime
from pprint import pprint

# -------- MBTA CONFIG --------
ROUTE_ID = "116"
STOP_ID  = "5733"           # fill this in
API_KEY  = "fd7a24507d4e45208098234176abc0b7"           # if you have one

# -------- MBTA ENDPOINT --------
URL = (
    "https://api-v3.mbta.com/predictions"
    f"?filter[route]={ROUTE_ID}"
    f"&filter[stop]={STOP_ID}"
    "&sort=departure_time"
    "&page[limit]=4"
    "&fields[prediction]=departure_time"
)

headers = {"accept": "application/json"}
if API_KEY:
    headers["x-api-key"] = API_KEY


def minutes_until(iso_str):
    """Convert MBTA ISO timestamp to minutes from now."""
    # Example: 2025-11-13T23:18:05-05:00
    dt = datetime.datetime.fromisoformat(iso_str)
    now = datetime.datetime.now(dt.tzinfo)
    delta = dt - now
    return int(delta.total_seconds() / 60)


def main():
    print("Calling MBTA API...")
    r = requests.get(URL, headers=headers)
    
    print(f"HTTP {r.status_code}")
    if r.status_code != 200:
        print("Error:")
        print(r.text)
        return

    data = r.json()

    # Pretty-print raw response (optional)
    print("\n--- Raw Data (first 2 entries) ---")
    pprint(data.get("data", [])[:2])

    # Extract departure times
    print("\n--- Parsed Results ---")
    predictions = []
    for item in data.get("data", []):
        attr = item.get("attributes", {})
        t = attr.get("departure_time") or attr.get("arrival_time")
        if t:
            predictions.append(t)

    if not predictions:
        print("No predictions found.")
        return

    # Show minutes until arrivals
    for i, iso in enumerate(predictions[:2]):
        mins = minutes_until(iso)
        label = "Next" if i == 0 else "Then"
        print(f"{label}: {mins} min (timestamp {iso})")

    print("\nSuccess! API is working.")

if __name__ == "__main__":
    main()

# import requests
# print(requests.get(
#   "https://api-v3.mbta.com/predictions?filter[route]=Blue&filter[stop]=place-aport&filter[direction_id]=1"
# ).json())