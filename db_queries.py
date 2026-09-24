import sqlite3

import pandas as pd
from pathlib import Path
import streamlit as st

# Shared config lives here rather than in each page so that the DB path and
# SA's team ID have exactly one definition — change it in one place, both
# pages pick it up.

DB_PATH = "bafana_bafana_wc.db"
SA_ID = "43883"

DB_PATH = Path(__file__).resolve().parent / "bafana_bafana_wc.db"


# A single choke-point for DB access. Every query in the app goes through
# here, which means caching is applied consistently and pages never open
# their own connections.

@st.cache_data
def run_query(sql, params=()):
    con = sqlite3.connect(DB_PATH)
    try:
        return pd.read_sql_query(sql, con, params=params)
    finally:
        con.close()


# Years come from the data, not a hardcoded list, so adding a new tournament
# to the DB is enough to make it appear in every dropdown.
@st.cache_data
def get_years():
    df = run_query("SELECT DISTINCT year FROM matches ORDER BY year")
    return df["year"].tolist()