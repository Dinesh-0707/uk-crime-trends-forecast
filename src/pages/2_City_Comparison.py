import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st
from data_access import load_totals

st.set_page_config(page_title="City Comparison", layout="wide", page_icon="📍")
st.title("City Comparison")
st.caption("Year-on-year change and relative ranking across cities.")

totals = load_totals()

pivot = totals.pivot(index="month", columns="city", values="total").sort_index()
yoy = pivot.pct_change(periods=12) * 100

latest_month = pivot.index.max()
if latest_month in yoy.index:
    latest_yoy = yoy.loc[latest_month].dropna().sort_values(ascending=False)
    st.subheader(f"Year-on-year % change — {latest_month.strftime('%B %Y')}")
    if latest_yoy.empty:
        st.info("Not enough history yet for a 12-month comparison on this data window.")
    else:
        chart_df = latest_yoy.rename("yoy_pct_change").rename_axis("city").reset_index()
        st.bar_chart(chart_df, x="city", y="yoy_pct_change")
else:
    st.info("Not enough history yet for a year-on-year comparison.")

st.subheader("Ranking by latest month total")
latest_totals = totals[totals["month"] == latest_month].sort_values("total", ascending=False)
latest_totals = latest_totals.reset_index(drop=True)
latest_totals.index = latest_totals.index + 1
st.dataframe(
    latest_totals[["city", "total"]].rename(columns={"total": "reported incidents"}),
    use_container_width=True,
)

st.subheader("All cities, indexed to first month = 100")
indexed = pivot.div(pivot.iloc[0]) * 100
st.line_chart(indexed)
