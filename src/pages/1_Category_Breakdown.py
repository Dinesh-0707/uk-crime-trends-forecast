import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st
from data_access import load_monthly

st.set_page_config(page_title="Category Breakdown", layout="wide", page_icon="📍")
st.title("Category Breakdown")
st.caption("What's driving each city's reported crime volume, by category.")

monthly = load_monthly()
cities = sorted(monthly["city"].unique())
city = st.selectbox("City", cities)

city_df = monthly[monthly["city"] == city]
latest_month = city_df["month"].max()
latest = city_df[city_df["month"] == latest_month].sort_values("count", ascending=False)

st.subheader(f"{city} — category share, {latest_month.strftime('%B %Y')}")
st.bar_chart(latest.set_index("category")["count"])

st.subheader("Category trend over time")
top_categories = latest.head(6)["category"].tolist()
trend = city_df[city_df["category"].isin(top_categories)]
pivot = trend.pivot(index="month", columns="category", values="count").fillna(0)
st.line_chart(pivot)

st.subheader("Raw monthly table")
table = latest[["category", "count"]].reset_index(drop=True)
table["share_of_total"] = (table["count"] / table["count"].sum() * 100).round(1).astype(str) + "%"
st.dataframe(table, use_container_width=True, hide_index=True)
