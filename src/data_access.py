"""Shared data loading helpers used by the app and its pages."""
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

DB_FILE = Path(__file__).resolve().parent.parent / "data" / "crime.db"


@st.cache_data
def load_totals() -> pd.DataFrame:
    with sqlite3.connect(DB_FILE) as conn:
        return pd.read_sql("SELECT * FROM crime_totals", conn, parse_dates=["month"])


@st.cache_data
def load_monthly() -> pd.DataFrame:
    with sqlite3.connect(DB_FILE) as conn:
        return pd.read_sql("SELECT * FROM crime_monthly", conn, parse_dates=["month"])
