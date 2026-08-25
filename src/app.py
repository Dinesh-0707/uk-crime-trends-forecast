"""
UK City Crime Trends — Overview page.

Business framing: a local authority / insurer / retail loss-prevention team
needs a quick read on how reported crime volume is trending across major
UK cities, to prioritise resourcing or risk pricing.

Run locally:
    streamlit run src/app.py

Deploy for free:
    Push this repo to GitHub, then deploy on share.streamlit.io with main
    file src/app.py.
"""
from pathlib import Path

import streamlit as st
from data_access import load_totals

st.set_page_config(page_title="UK City Crime Trends", layout="wide", page_icon="📍")

st.title("UK City Crime Trends")
st.caption(
    "Source: data.police.uk public API (live, street-level incident data). "
    "Built with Python, pandas, SQLite and Streamlit."
)

totals = load_totals()
cities = sorted(totals["city"].unique())
selected = st.multiselect("Cities", cities, default=cities)
filtered = totals[totals["city"].isin(selected)]

latest_month = filtered["month"].max()
latest = filtered[filtered["month"] == latest_month].sort_values("total", ascending=False)
prev_month_data = filtered[filtered["month"] == sorted(filtered["month"].unique())[-2]] if filtered["month"].nunique() > 1 else None

cols = st.columns(len(latest)) if len(latest) else []
for col, (_, row) in zip(cols, latest.iterrows()):
    prev = None
    if prev_month_data is not None:
        prev_row = prev_month_data[prev_month_data["city"] == row["city"]]
        if not prev_row.empty:
            prev = prev_row["total"].iloc[0]
    delta = f"{row['total'] - prev:+,.0f} vs prior month" if prev is not None else None
    col.metric(row["city"], f"{row['total']:,.0f}", delta)

st.caption(f"Latest month in dataset: {latest_month.strftime('%B %Y')}")

st.subheader("Monthly reported crime volume")
pivot = filtered.pivot(index="month", columns="city", values="total")
st.line_chart(pivot)

with st.expander("How to read this"):
    st.markdown(
        "- Counts are **reported incidents within roughly 1 mile of each city centre**, "
        "not city-wide totals — useful for relative comparison and trend direction, "
        "not absolute city crime rates.\n"
        "- See **Category Breakdown** for what's driving each city's volume, "
        "**City Comparison** for year-on-year change, and **Forecast** for a "
        "3-month projection per city."
    )

st.page_link("pages/1_Category_Breakdown.py", label="→ Category Breakdown")
st.page_link("pages/2_City_Comparison.py", label="→ City Comparison")
st.page_link("pages/3_Forecast.py", label="→ Forecast")
