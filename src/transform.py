"""
Cleans the raw crime extract into a SQLite warehouse (data/crime.db) with
two analysis-ready tables:
  - crime_monthly: city, month, category, count
  - crime_totals:  city, month, total  (sum across categories)
"""
import sqlite3
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RAW_FILE = DATA_DIR / "crime_raw.csv"
DB_FILE = DATA_DIR / "crime.db"


def main():
    df = pd.read_csv(RAW_FILE)
    df["month"] = pd.to_datetime(df["month"], format="%Y-%m")
    df["count"] = pd.to_numeric(df["count"], errors="coerce").fillna(0).astype(int)
    df = df.dropna(subset=["city", "category"])
    df = df.drop_duplicates(subset=["city", "month", "category"])
    df = df.sort_values(["city", "month", "category"]).reset_index(drop=True)

    totals = (
        df.groupby(["city", "month"], as_index=False)["count"]
        .sum()
        .rename(columns={"count": "total"})
        .sort_values(["city", "month"])
    )

    with sqlite3.connect(DB_FILE) as conn:
        df.to_sql("crime_monthly", conn, if_exists="replace", index=False)
        totals.to_sql("crime_totals", conn, if_exists="replace", index=False)

    print(f"Loaded {len(df)} category rows and {len(totals)} monthly totals -> {DB_FILE}")


if __name__ == "__main__":
    main()
