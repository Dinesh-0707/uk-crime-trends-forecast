"""
Pulls street-level crime data from the UK Police public API (data.police.uk,
no key required) for a set of major UK cities over the last N months, and
writes a monthly category-count table to data/crime_raw.csv.

The API returns individual incident records within ~1 mile of a lat/lng for
a given month; we aggregate to (city, month, category, count) here so the
downstream warehouse stays small and analysis-ready.

API docs: https://data.police.uk/docs/
"""
import csv
import json
import subprocess
import time
from collections import Counter
from pathlib import Path
from urllib.parse import urlencode

CITIES = {
    "Birmingham": (52.4862, -1.8904),
    "London": (51.5074, -0.1278),
    "Liverpool": (53.4084, -2.9916),
    "Leeds": (53.8008, -1.5491),
    "Bristol": (51.4545, -2.5879),
}
# Note: Greater Manchester Police's feed on this API is known to return only
# a handful of records per month regardless of query point (a long-standing
# GMP data-quality issue, not a bug here) — Liverpool used instead.

BASE_URL = "https://data.police.uk/api/crimes-street/all-crime"
DATES_URL = "https://data.police.uk/api/crimes-street-dates"

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUT_FILE = DATA_DIR / "crime_raw.csv"


def _get_json(url: str, params: dict = None):
    """
    Fetch JSON via curl rather than `requests`. Some environments ship a
    Python `ssl` module built against an old LibreSSL that fails the TLS
    handshake with this API (TLSV1_ALERT_PROTOCOL_VERSION) even though the
    server is fine — curl negotiates it without issue. If you're on a
    machine with a modern OpenSSL, swap this for `requests.get(...).json()`.
    """
    full_url = f"{url}?{urlencode(params)}" if params else url
    for attempt in range(3):
        result = subprocess.run(
            ["curl", "-s", "--max-time", "30", "--retry", "2", full_url],
            capture_output=True, text=True,
        )
        if result.returncode == 0 and result.stdout:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                pass
        time.sleep(2 * (attempt + 1))
    return None


def available_months(limit: int = 24) -> list:
    dates = _get_json(DATES_URL)
    if not dates:
        raise SystemExit("Could not reach data.police.uk to list available months.")
    return [d["date"] for d in dates][:limit]


def fetch_counts(lat: float, lng: float, month: str) -> Counter:
    records = _get_json(BASE_URL, {"lat": lat, "lng": lng, "date": month})
    if not isinstance(records, list):
        return Counter()
    return Counter(r.get("category", "unknown") for r in records)


def main(months_back: int = 24):
    months = available_months(months_back)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    for city, (lat, lng) in CITIES.items():
        for month in months:
            counts = fetch_counts(lat, lng, month)
            for category, count in counts.items():
                rows.append({"city": city, "month": month, "category": category, "count": count})
            print(f"{city} {month}: {sum(counts.values())} incidents")
            time.sleep(0.5)

    if not rows:
        raise SystemExit("No data retrieved — check network access or API availability.")

    with OUT_FILE.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["city", "month", "category", "count"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWrote {len(rows)} rows to {OUT_FILE}")


if __name__ == "__main__":
    main()
