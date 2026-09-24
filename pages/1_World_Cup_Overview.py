import pandas as pd
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db_queries import get_years, run_query


# --- Queries specific to this page ---
@st.cache_data
def get_tournament_summary(year):
    return run_query(
        """
        SELECT
            COUNT(*)                                              AS total_matches,
            SUM(COALESCE(home_score, 0) + COALESCE(away_score, 0)) AS total_goals,
            AVG(attendance)                                       AS avg_attendance,
            COUNT(DISTINCT home_team_id) + COUNT(DISTINCT away_team_id) AS team_appearances
        FROM matches
        WHERE year = ?
        """,
        (year,),
    ).iloc[0]


@st.cache_data
def get_all_matches_for_year(year):
    return run_query(
        """
        SELECT
            m.date,
            m.stage,
            m.group_name,
            ht.name AS home_team,
            m.home_score,
            at.name AS away_team,
            m.away_score,
            m.stadium,
            m.attendance
        FROM matches AS m
        LEFT JOIN teams AS ht ON m.home_team_id = ht.id_team AND m.year = ht.year
        LEFT JOIN teams AS at ON m.away_team_id = at.id_team AND m.year = at.year
        WHERE m.year = ?
        ORDER BY m.date
        """,
        (year,),
    )


# --- Helpers ---
def format_date(value):
    parsed = pd.to_datetime(value, errors="coerce")
    return parsed.strftime("%b %d") if pd.notna(parsed) else "—"


def format_score(home, away):
    if pd.isna(home) or pd.isna(away):
        return "—"
    return f"{int(home)}–{int(away)}"


def format_attendance(value):
    return f"{value:,.0f}" if pd.notna(value) else "—"


# --- Page ---
st.set_page_config(page_title="World Cup Overview", layout="wide")

years = get_years()
if not years:
    st.error("No rows in `matches`.")
    st.stop()

title_col, selector_col = st.columns([4, 1])
with title_col:
    st.title("FIFA World Cup — Tournament Overview")
    st.markdown(
        "Tournament-wide stats for every World Cup in the database. "
        "For South Africa's story, head back to the main page."
    )
with selector_col:
    year = st.selectbox("Pick a year", years, index=0)

# --- Tournament-wide KPI cards ---
summary = get_tournament_summary(year)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total matches", f"{int(summary['total_matches'])}")
c2.metric("Total goals", f"{int(summary['total_goals'] or 0)}")
c3.metric("Avg attendance", format_attendance(summary["avg_attendance"]))
c4.metric("Team appearances", f"{int(summary['team_appearances'])}")

st.divider()

# --- All matches for the year ---
st.subheader(f"All matches — {year}")

matches_df = get_all_matches_for_year(year)

if matches_df.empty:
    st.info(f"No matches loaded for {year}.")
else:
    display = matches_df.copy()
    display["Date"] = display["date"].apply(format_date)
    display["Score"] = display.apply(
        lambda r: format_score(r["home_score"], r["away_score"]), axis=1
    )
    display["Attendance"] = display["attendance"].apply(format_attendance)
    display = display.rename(columns={
        "home_team": "Home",
        "away_team": "Away",
        "stage": "Stage",
        "group_name": "Group",
        "stadium": "Stadium",
    })
    st.dataframe(
        display[["Date", "Home", "Score", "Away", "Stage", "Group", "Stadium", "Attendance"]],
        hide_index=True,
        use_container_width=True,
    )

st.markdown("---")
st.caption("© 2026 by uamahlecele.")