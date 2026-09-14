import sqlite3
import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# PAGE CONFIG — must be the first Streamlit command
# ---------------------------------------------------------------------------
st.set_page_config(page_title="iBafana Bafana & the World Cup", layout="wide")

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
DB_PATH = "bafana_bafana_wc.db"
SOUTH_AFRICA_ID = "43883"  # FIFA numeric id — same string in every year's teams row

# ---------------------------------------------------------------------------
# QUERY LAYER — every function is parameterised, nothing is hardcoded to a year
# ---------------------------------------------------------------------------


@st.cache_data
def run_query(sql, params=()):
    """Single choke-point for DB access so every query gets cached the same way."""
    con = sqlite3.connect(DB_PATH)
    try:
        return pd.read_sql_query(sql, con, params=params)
    finally:
        con.close()


@st.cache_data
def get_years():
    """Drives the year selector. Never hardcode the year list."""
    df = run_query("SELECT DISTINCT year FROM matches ORDER BY year DESC")
    return df["year"].tolist()


@st.cache_data
def get_year_summary(year):
    """One row: total matches, total goals, average attendance for the year."""
    df = run_query(
        """
        SELECT COUNT(*)                                                  AS total_matches,
               SUM(COALESCE(home_score, 0) + COALESCE(away_score, 0))    AS total_goals,
               AVG(attendance)                                           AS avg_attendance
        FROM matches
        WHERE year = ?
        """,
        (year,),
    )
    return df.iloc[0]


@st.cache_data
def get_matches_for_year(year):
    """
    Match list with real team names.

    NOTE: the join matches on id_team AND year. Joining on id_team alone would
    attach a team's row from a different tournament to this match.
    """
    return run_query(
        """
        SELECT m.date,
               m.stage,
               m.group_name,
               ht.name AS home_team,
               m.home_score,
               at.name AS away_team,
               m.away_score,
               m.stadium,
               m.attendance
        FROM matches AS m
        LEFT JOIN teams AS ht
               ON m.home_team_id = ht.id_team AND m.year = ht.year
        LEFT JOIN teams AS at
               ON m.away_team_id = at.id_team AND m.year = at.year
        WHERE m.year = ?
        ORDER BY m.date
        """,
        (year,),
    )


@st.cache_data
def get_south_africa_by_year():
    """South Africa's tournament-by-tournament record, across every loaded year."""
    return run_query(
        """
        SELECT m.year,
               COUNT(*) AS matches_played,
               SUM(CASE WHEN m.winner_id = ? THEN 1 ELSE 0 END) AS wins,
               SUM(CASE WHEN m.home_team_id = ?
                        THEN COALESCE(m.home_score, 0)
                        ELSE COALESCE(m.away_score, 0) END) AS goals_for
        FROM matches AS m
        WHERE m.home_team_id = ? OR m.away_team_id = ?
        GROUP BY m.year
        ORDER BY m.year
        """,
        (SOUTH_AFRICA_ID, SOUTH_AFRICA_ID, SOUTH_AFRICA_ID, SOUTH_AFRICA_ID),
    )


# ---------------------------------------------------------------------------
# HELPERS — presentation only, no DB access
# ---------------------------------------------------------------------------


def format_score(row):
    if pd.isna(row["home_score"]) or pd.isna(row["away_score"]):
        return "—"
    return f"{int(row['home_score'])} - {int(row['away_score'])}"


def format_date(value):
    parsed = pd.to_datetime(value, errors="coerce", utc=True)
    return parsed.strftime("%b %d") if pd.notna(parsed) else "—"


def format_attendance(value):
    return f"{value:,.0f}" if pd.notna(value) else "—"


# ---------------------------------------------------------------------------
# HEADER
# ---------------------------------------------------------------------------
st.title("Bafana Bafana's All Time Performance at the FIFA World Cup")
st.markdown(
    "Tracking South Africa's Football Team performance in the FIFA World Cup "
    "from their debut in 1998 onwards."
)

# ---------------------------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------------------------
years = get_years()
if not years:
    st.error(f"No rows found in `matches`. Has anything been loaded into {DB_PATH}?")
    st.stop()

# --- header row: title on the left, year selector on the right --------------
title_col, selector_col = st.columns([3, 1])
with title_col:
    st.subheader("World Cup stats explorer")
with selector_col:
    year = st.selectbox("Select year", years)

# --- metric cards -----------------------------------------------------------
summary = get_year_summary(year)

metric_cols = st.columns(3)
metric_cols[0].metric("Total matches", f"{int(summary['total_matches']):,}")
metric_cols[1].metric("Total goals", f"{int(summary['total_goals'] or 0):,}")
metric_cols[2].metric("Avg attendance", format_attendance(summary["avg_attendance"]))

# --- South Africa across all years ------------------------------------------
st.markdown("**South Africa results — all years**")

sa_df = get_south_africa_by_year()

if sa_df.empty:
    st.info("No South Africa matches found in the database.")
else:
    chart_df = sa_df.set_index("year")[["goals_for"]].rename(
        columns={"goals_for": "Goals scored"}
    )
    st.bar_chart(chart_df)

    with st.expander("Full record by tournament"):
        st.dataframe(sa_df, hide_index=True, use_container_width=True)

# --- matches for the selected year ------------------------------------------
st.markdown(f"**Matches — {year}**")

matches_df = get_matches_for_year(year)

if matches_df.empty:
    st.info(f"No matches loaded for {year}.")
else:
    display_df = matches_df.copy()
    display_df["Date"] = display_df["date"].apply(format_date)
    display_df["Score"] = display_df.apply(format_score, axis=1)
    display_df["Attendance"] = display_df["attendance"].apply(format_attendance)

    display_df = display_df.rename(
        columns={
            "home_team": "Home",
            "away_team": "Away",
            "stage": "Stage",
            "group_name": "Group",
            "stadium": "Stadium",
        }
    )

    st.dataframe(
        display_df[["Date", "Home", "Score", "Away", "Stage", "Group", "Stadium", "Attendance"]],
        hide_index=True,
        use_container_width=True,
    )

# ---------------------------------------------------------------------------
# FOOTER
# ---------------------------------------------------------------------------
st.markdown("---")
st.caption("© 2026 by uamahlecele.")