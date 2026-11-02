# UK City Crime Trends & Forecast

A multi-page Python data app tracking reported crime volume across five UK
cities, with a statistical forecast layer — built to show depth beyond a
single dashboard: live ETL, a SQL warehouse, and an applied forecasting
model, not just a chart.

**Business framing:** a local authority, insurer, or retail loss-prevention
team needs a fast read on which cities are trending up or down in reported
incidents, what's driving the volume, and where it's headed next quarter.

## Pages
1. **Overview** — KPI cards + trend lines across cities.
2. **Category Breakdown** — what's driving each city's volume (burglary,
   violent crime, anti-social behaviour, etc.), trend by category.
3. **City Comparison** — year-on-year % change, ranking, indexed comparison.
4. **Forecast** — 3-month projection per city using Holt's linear trend
   exponential smoothing (statsmodels), with a plain-language reading of
   the direction and magnitude.

## Pipeline
1. `src/extract.py` — pulls live incident data from the UK Police public API
   (`data.police.uk`, no key required) for 5 cities over the last 24 months,
   aggregated to (city, month, category, count).
2. `src/transform.py` — cleans and loads into a SQLite warehouse
   (`data/crime.db`): `crime_monthly` (by category) and `crime_totals`
   (city-month totals).
3. `src/app.py` + `src/pages/` — the Streamlit multi-page app.

**Note on data:** counts are reported incidents within ~1 mile of each
city's centre point (the API's search radius), not city-wide totals —
useful for relative trend comparison, not as an absolute crime-rate figure.
Greater Manchester's feed on this API has a known long-standing data-quality
gap (returns only a handful of records regardless of query location), so
Liverpool is used in its place.

## Run it locally
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python src/extract.py
python src/transform.py
streamlit run src/app.py
```
If your Python's SSL library is too old to negotiate TLS with
`data.police.uk` (you'll see `TLSV1_ALERT_PROTOCOL_VERSION`), `extract.py`
already routes requests through `curl` instead of `requests` to work around
it — see the comment in `src/extract.py`.

## Deployment
Live on Streamlit Community Cloud:
[uk-crime-trends-forecast.streamlit.app](https://uk-crime-trends-forecast-2km7uvnzwmqwdkwnj6xu4s.streamlit.app/).
`data/crime.db` is committed, so the hosted app doesn't re-run the extract
step on startup.

## Design choices
- **Live API → SQL warehouse → app**, the same pattern as the
  [house price monitor](https://github.com/Dinesh-0707/uk-house-price-dashboard),
  applied to a different domain.
- **Holt's linear trend** exponential smoothing for the 3-month forecast,
  fitted per city on monthly totals.
- **Multi-page app** so each question (overview, categories, comparison,
  forecast) has its own page.
