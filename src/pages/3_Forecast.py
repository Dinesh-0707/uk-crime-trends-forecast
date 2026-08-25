import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st
from data_access import load_totals

st.set_page_config(page_title="Forecast", layout="wide", page_icon="📍")
st.title("3-Month Forecast")
st.caption(
    "Holt's linear trend exponential smoothing, fit per city on the monthly "
    "reported-incident series. A simple, defensible baseline forecast — not "
    "a claim of precision, but enough to flag which cities are trending up."
)

totals = load_totals()
cities = sorted(totals["city"].unique())
city = st.selectbox("City", cities)

series = (
    totals[totals["city"] == city]
    .sort_values("month")
    .set_index("month")["total"]
    .asfreq("MS")
    .interpolate()
)

HORIZON = 3

try:
    from statsmodels.tsa.holtwinters import Holt

    model = Holt(series, initialization_method="estimated").fit()
    forecast = model.forecast(HORIZON)
    method = "Holt's linear trend (statsmodels)"
except Exception:
    # Fallback if statsmodels isn't available in the deploy environment:
    # simple linear extrapolation on the last 6 points.
    recent = series.tail(6)
    x = range(len(recent))
    slope = (recent.iloc[-1] - recent.iloc[0]) / max(len(recent) - 1, 1)
    last_val = recent.iloc[-1]
    future_index = pd.date_range(series.index[-1] + pd.DateOffset(months=1), periods=HORIZON, freq="MS")
    forecast = pd.Series([last_val + slope * (i + 1) for i in range(HORIZON)], index=future_index)
    method = "linear extrapolation (fallback — statsmodels unavailable)"

st.caption(f"Method: {method}")

combined = pd.concat([series.rename("actual"), forecast.rename("forecast")], axis=1)
combined = combined.rename_axis("month").reset_index()
combined["month"] = pd.to_datetime(combined["month"])
st.line_chart(combined, x="month", y=["actual", "forecast"])

st.subheader("Forecasted values")
forecast_table = forecast.reset_index()
forecast_table.columns = ["month", "forecasted incidents"]
forecast_table["month"] = forecast_table["month"].dt.strftime("%B %Y")
forecast_table["forecasted incidents"] = forecast_table["forecasted incidents"].round(0).astype(int)
st.dataframe(forecast_table, use_container_width=True, hide_index=True)

last_actual = series.iloc[-1]
next_forecast = forecast.iloc[0]
direction = "up" if next_forecast > last_actual else "down"
pct = abs(next_forecast - last_actual) / last_actual * 100 if last_actual else 0
st.markdown(
    f"**Reading:** {city}'s reported incidents are projected to trend "
    f"**{direction} ~{pct:.1f}%** next month versus the latest actual "
    f"({last_actual:,.0f} → {next_forecast:,.0f})."
)
