import sqlite3

import altair as alt
import pandas as pd
import streamlit as st

# --- Config ---
DB_PATH = "bafana_bafana_wc.db"
SA_ID = "43883"  # South Africa's FIFA numeric team ID, used to filter every query

RESULT_BADGE = {"Win": "W", "Draw": "D", "Loss": "L"}

SYNOPSIS = {
    1998: (
        "South Africa made their historic FIFA World Cup debut at France 1998 "
        "just six years after being readmitted to international football "
        "following the end of apartheid. Fresh off winning the 1996 Africa Cup "
        "of Nations and qualifying under coach Clive Barker, the team entered "
        "the tournament carrying immense national pride, though under the "
        "rushed guidance of newly appointed manager Philippe Troussier."
    ),
    2002: "Following their emotional debut in 1998, South Africa arrived in Asia as"
    " a far more seasoned and mature team. Managed by local football icon Jomo Sono, the team boasted world-class talent, "
    "including the defensive resilience of captain Lucas Radebe, the flair of Quinton Fortune,"
    " and the clinical striking abilities of Benni McCarthy. "
    "There was a genuine, realistic belief that this group had the quality to progress past the opening phase.",
     
    2010: "Automatically qualified as hosts, Bafana Bafana entered the tournament under immense emotional pressure"
    " and the watchful eye of a hopeful continent. Managed by veteran Brazilian coach Carlos Alberto Parreira, "
    "the squad was a mix of reliable domestic stars and European-based talent, "
    "captained by Aaron Mokoena and anchored by the creative brilliance of Teko Modise and Steven Pienaar. "
    "The primary mission was clear: harness home-ground advantage to break out of a daunting group.", 

    2026: "The 2026 FIFA World Cup campaign in Canada, Mexico, and the United States marked a monumental breakthrough, "
    "rewriting South African football history. Led by veteran Belgian tactician Hugo Broos, "
    "Bafana Bafana did what no senior men's team before them could accomplish: they advanced out of the group stage at a World Cup."
    "After a devastating 16-year absence from football's biggest stage, South Africa secured qualification through a rigorous CAF campaign, edgeing out rivals like Nigeria. Entering the expanded 48-team tournament, Broos relied on a highly unified, disciplined squad composed heavily of domestic stars—many fresh off a third-place finish at the 2023 Africa Cup of Nations. The focus shifted from hoping for individual brilliance to executing a rigid, fiercely resilient team ethic.",  
}


# --- Query layer ---
# All SQLite access goes through these functions, cached so Streamlit
# doesn't re-hit the database on every widget interaction.

@st.cache_data
def run_query(sql, params=()):
    con = sqlite3.connect(DB_PATH)
    try:
        return pd.read_sql_query(sql, con, params=params)
    finally:
        con.close()


@st.cache_data
def get_years():
    # Powers the year dropdown - pulled from the data so it updates
    # automatically if more tournaments get added later.
    df = run_query("SELECT DISTINCT year FROM matches ORDER BY year")
    return df["year"].tolist()


@st.cache_data
def get_sa_by_year():
    # One row per tournament: matches played, goals, and win/draw/loss record.
    # Feeds both the KPI cards and the goals-per-tournament chart.
    return run_query(
        """
        SELECT
            m.year,
            COUNT(*) AS matches_played,
            SUM(CASE WHEN m.home_team_id = ? THEN m.home_score ELSE m.away_score END) AS goals_scored,
            SUM(CASE WHEN m.home_team_id = ? THEN m.away_score ELSE m.home_score END) AS goals_conceded,
            SUM(CASE WHEN m.winner_id = ? THEN 1 ELSE 0 END) AS wins,
            SUM(CASE WHEN m.winner_id IS NULL OR m.winner_id = '' THEN 1 ELSE 0 END) AS draws,
            SUM(CASE WHEN m.winner_id IS NOT NULL AND m.winner_id <> ''
                      AND m.winner_id <> ? THEN 1 ELSE 0 END) AS losses
        FROM matches AS m
        WHERE m.home_team_id = ? OR m.away_team_id = ?
        GROUP BY m.year
        ORDER BY m.year
        """,
        (SA_ID, SA_ID, SA_ID, SA_ID, SA_ID, SA_ID),
    )


@st.cache_data
def get_sa_matches_for_year(year):
    # South Africa's individual matches for one tournament, always written
    # from SA's perspective (opponent, SA's score, opponent's score) rather
    # than raw home/away, since SA isn't always the "home" side in the data.
    return run_query(
        """
        SELECT
            m.date,
            m.stage,
            m.stadium,
            CASE WHEN m.home_team_id = ? THEN at.name ELSE ht.name END AS opponent,
            CASE
                WHEN m.winner_id = ? THEN 'Win'
                WHEN m.winner_id IS NULL OR m.winner_id = '' THEN 'Draw'
                ELSE 'Loss'
            END AS result,
            CASE WHEN m.home_team_id = ? THEN m.home_score ELSE m.away_score END AS sa_score,
            CASE WHEN m.home_team_id = ? THEN m.away_score ELSE m.home_score END AS opponent_score
        FROM matches AS m
        LEFT JOIN teams AS ht ON m.home_team_id = ht.id_team AND m.year = ht.year
        LEFT JOIN teams AS at ON m.away_team_id = at.id_team AND m.year = at.year
        WHERE (m.home_team_id = ? OR m.away_team_id = ?)
          AND m.year = ?
        ORDER BY m.date
        """,
        (SA_ID, SA_ID, SA_ID, SA_ID, SA_ID, SA_ID, year),
    )


# --- Formatting helpers ---
# Turn raw query output into the strings actually shown in the table.

def format_date(value):
    parsed = pd.to_datetime(value, errors="coerce")
    return parsed.strftime("%b %d") if pd.notna(parsed) else "—"


def format_score(row):
    if pd.isna(row["sa_score"]) or pd.isna(row["opponent_score"]):
        return "—"
    return f"{int(row['sa_score'])}–{int(row['opponent_score'])}"


def format_matches_for_display(df):
    display = df.copy()
    display["Date"] = display["date"].apply(format_date)
    display["Score"] = display.apply(format_score, axis=1)
    display["Result"] = display["result"].map(RESULT_BADGE)
    display = display.rename(columns={
        "opponent": "Opponent",
        "stage": "Stage",
        "stadium": "Stadium",
    })
    return display[["Date", "Opponent", "Score", "Result", "Stage", "Stadium"]]


# --- Page setup ---
st.set_page_config(page_title="iBafana Bafana — World Cup history", layout="wide")

years = get_years()
if not years:
    st.error(f"No rows in `matches`. Has anything been loaded into {DB_PATH}?")
    st.stop()

sa_by_year = get_sa_by_year()

# --- Header + year selector ---
title_col, selector_col = st.columns([4, 1])
with title_col:
    st.title("Bafana Bafana's All Time Performance at the FIFA World Cup")
    st.markdown(
        "Tracking South Africa's Football Team performance in the FIFA World Cup "
        "from their debut in 1998 onwards."
    )
with selector_col:
    year = st.selectbox("Pick a year", years, index=0)

# --- KPI cards for the selected year ---
row = sa_by_year[sa_by_year["year"] == year].iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Matches played", int(row["matches_played"]))
c2.metric("Goals scored", int(row["goals_scored"]))
c3.metric("Goals conceded", int(row["goals_conceded"]))
c4.metric(
    "Record",
    f"{int(row['wins'])}W · {int(row['draws'])}D · {int(row['losses'])}L",
)

st.divider()

# --- Goals per tournament chart ---
# Shows all tournaments for context, with the selected year highlighted.
st.subheader("Goals scored per tournament")
st.caption("Selected tournament is highlighted. Bars show all tournaments for context.")

chart_df = sa_by_year.copy()
chart_df["is_selected"] = chart_df["year"] == year

bars = (
    alt.Chart(chart_df)
    .mark_bar(size=52, cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
    .encode(
        x=alt.X("year:O", title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("goals_scored:Q", title="Goals scored"),
        color=alt.condition(
            alt.datum.is_selected,
            alt.value("#B08D57"),  # bronze/gold - selected tournament
            alt.value("#D8CDB0"),  # muted parchment - other tournaments
        ),
        tooltip=[
            alt.Tooltip("year:O", title="Tournament"),
            alt.Tooltip("goals_scored:Q", title="Goals scored"),
            alt.Tooltip("goals_conceded:Q", title="Goals conceded"),
            alt.Tooltip("matches_played:Q", title="Matches"),
        ],
    )
)

labels = bars.mark_text(dy=-10, color="#2B3A2E", fontSize=13).encode(
    text=alt.Text("goals_scored:Q")
)

labels = bars.mark_text(dy=-10, color="#333", fontSize=13).encode(
    text=alt.Text("goals_scored:Q")
)

st.altair_chart(bars + labels, use_container_width=True)

st.divider()

# --- Match table for the selected year ---
st.subheader(f"Matches — {year}")

# --- Synopsis for the selected year ---
synopsis = SYNOPSIS.get(year)
if synopsis:
    st.markdown(f"> {synopsis}")
    st.write("")

matches_df = get_sa_matches_for_year(year)

if matches_df.empty:
    st.info(f"No South Africa matches loaded for {year}.")
else:
    st.dataframe(
        format_matches_for_display(matches_df),
        hide_index=True,
        use_container_width=True,
    )

st.markdown("---")
st.caption("© 2026 by uamahlecele.")







# import sqlite3

# import altair as alt
# import pandas as pd
# import plotly.express as px
# import streamlit as st

# # --- Config ---
# DB_PATH = "bafana_bafana_wc.db"
# SA_ID = "43883"  # South Africa's FIFA numeric team ID, used to filter every query

# RESULT_BADGE = {"Win": "W", "Draw": "D", "Loss": "L"}

# # Host nations per tournament. Hardcoded because there's no hosts table yet —
# # only 4 rows, and the source CSVs don't carry host metadata.
# # ISO-3 codes are used instead of country names because names are fragile
# # ("United States" vs "USA" vs "United States of America" all fail differently).
# HOST_COUNTRIES = {
#     1998: [("FRA", "France")],
#     2002: [("KOR", "South Korea"), ("JPN", "Japan")],
#     2010: [("ZAF", "South Africa")],
#     2026: [("USA", "United States"), ("CAN", "Canada"), ("MEX", "Mexico")],
# }


# # --- Query layer ---
# @st.cache_data
# def run_query(sql, params=()):
#     con = sqlite3.connect(DB_PATH)
#     try:
#         return pd.read_sql_query(sql, con, params=params)
#     finally:
#         con.close()


# @st.cache_data
# def get_years():
#     df = run_query("SELECT DISTINCT year FROM matches ORDER BY year")
#     return df["year"].tolist()


# @st.cache_data
# def get_sa_by_year():
#     return run_query(
#         """
#         SELECT
#             m.year,
#             COUNT(*) AS matches_played,
#             SUM(CASE WHEN m.home_team_id = ? THEN m.home_score ELSE m.away_score END) AS goals_scored,
#             SUM(CASE WHEN m.home_team_id = ? THEN m.away_score ELSE m.home_score END) AS goals_conceded,
#             SUM(CASE WHEN m.winner_id = ? THEN 1 ELSE 0 END) AS wins,
#             SUM(CASE WHEN m.winner_id IS NULL OR m.winner_id = '' THEN 1 ELSE 0 END) AS draws,
#             SUM(CASE WHEN m.winner_id IS NOT NULL AND m.winner_id <> ''
#                       AND m.winner_id <> ? THEN 1 ELSE 0 END) AS losses
#         FROM matches AS m
#         WHERE m.home_team_id = ? OR m.away_team_id = ?
#         GROUP BY m.year
#         ORDER BY m.year
#         """,
#         (SA_ID, SA_ID, SA_ID, SA_ID, SA_ID, SA_ID),
#     )


# @st.cache_data
# def get_sa_matches_for_year(year):
#     return run_query(
#         """
#         SELECT
#             m.date,
#             m.stage,
#             m.stadium,
#             CASE WHEN m.home_team_id = ? THEN at.name ELSE ht.name END AS opponent,
#             CASE
#                 WHEN m.winner_id = ? THEN 'Win'
#                 WHEN m.winner_id IS NULL OR m.winner_id = '' THEN 'Draw'
#                 ELSE 'Loss'
#             END AS result,
#             CASE WHEN m.home_team_id = ? THEN m.home_score ELSE m.away_score END AS sa_score,
#             CASE WHEN m.home_team_id = ? THEN m.away_score ELSE m.home_score END AS opponent_score
#         FROM matches AS m
#         LEFT JOIN teams AS ht ON m.home_team_id = ht.id_team AND m.year = ht.year
#         LEFT JOIN teams AS at ON m.away_team_id = at.id_team AND m.year = at.year
#         WHERE (m.home_team_id = ? OR m.away_team_id = ?)
#           AND m.year = ?
#         ORDER BY m.date
#         """,
#         (SA_ID, SA_ID, SA_ID, SA_ID, SA_ID, SA_ID, year),
#     )


# # --- Formatting helpers ---
# def format_date(value):
#     parsed = pd.to_datetime(value, errors="coerce")
#     return parsed.strftime("%b %d") if pd.notna(parsed) else "—"


# def format_score(row):
#     if pd.isna(row["sa_score"]) or pd.isna(row["opponent_score"]):
#         return "—"
#     return f"{int(row['sa_score'])}–{int(row['opponent_score'])}"


# def format_matches_for_display(df):
#     display = df.copy()
#     display["Date"] = display["date"].apply(format_date)
#     display["Score"] = display.apply(format_score, axis=1)
#     display["Result"] = display["result"].map(RESULT_BADGE)
#     display = display.rename(columns={
#         "opponent": "Opponent",
#         "stage": "Stage",
#         "stadium": "Stadium",
#     })
#     return display[["Date", "Opponent", "Score", "Result", "Stage", "Stadium"]]


# # --- Map builder ---
# def build_host_map(year):
#     """Choropleth of the world with the selected year's host nation(s) highlighted."""
#     hosts = HOST_COUNTRIES.get(year, [])
#     if not hosts:
#         return None

#     host_df = pd.DataFrame(hosts, columns=["iso_alpha", "country"])
#     host_df["value"] = 1  # plotly needs a color column; all hosts share the same value

#     fig = px.choropleth(
#         host_df,
#         locations="iso_alpha",
#         color="value",
#         hover_name="country",
#         color_continuous_scale=["#29b6a3", "#29b6a3"],  # single flat color
#     )

#     fig.update_geos(
#         showframe=False,
#         showcoastlines=True,
#         coastlinecolor="#dcdcdc",
#         showland=True,
#         landcolor="#f5f5f5",
#         showcountries=True,
#         countrycolor="#e5e5e5",
#         projection_type="natural earth",
#     )

#     fig.update_coloraxes(showscale=False)
#     fig.update_layout(
#         margin=dict(l=0, r=0, t=0, b=0),
#         height=360,
#         paper_bgcolor="rgba(0,0,0,0)",
#         plot_bgcolor="rgba(0,0,0,0)",
#     )
#     return fig


# # --- Page setup ---
# st.set_page_config(page_title="iBafana Bafana — World Cup history", layout="wide")

# years = get_years()
# if not years:
#     st.error(f"No rows in `matches`. Has anything been loaded into {DB_PATH}?")
#     st.stop()

# sa_by_year = get_sa_by_year()

# # --- Header + year selector ---
# title_col, selector_col = st.columns([4, 1])
# with title_col:
#     st.title("Bafana Bafana's All Time Performance at the FIFA World Cup")
#     st.markdown(
#         "Tracking South Africa's Football Team performance in the FIFA World Cup "
#         "from their debut in 1998 onwards."
#     )
# with selector_col:
#     year = st.selectbox("Pick a year", years, index=0)

# # --- KPI cards for the selected year ---
# row = sa_by_year[sa_by_year["year"] == year].iloc[0]

# c1, c2, c3, c4 = st.columns(4)
# c1.metric("Matches played", int(row["matches_played"]))
# c2.metric("Goals scored", int(row["goals_scored"]))
# c3.metric("Goals conceded", int(row["goals_conceded"]))
# c4.metric(
#     "Record",
#     f"{int(row['wins'])}W · {int(row['draws'])}D · {int(row['losses'])}L",
# )

# st.divider()

# # --- Map + chart, side by side ---
# map_col, chart_col = st.columns([1, 1])

# with map_col:
#     st.subheader(f"Host nation — {year}")
#     host_fig = build_host_map(year)
#     if host_fig is None:
#         st.info(f"No host data defined for {year}.")
#     else:
#         st.plotly_chart(host_fig, use_container_width=True)

# with chart_col:
#     st.subheader("Goals scored per tournament")
#     st.caption("Selected tournament is highlighted.")

#     chart_df = sa_by_year.copy()
#     chart_df["is_selected"] = chart_df["year"] == year

#     bars = (
#         alt.Chart(chart_df)
#         .mark_bar(size=52, cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
#         .encode(
#             x=alt.X("year:O", title=None, axis=alt.Axis(labelAngle=0)),
#             y=alt.Y("goals_scored:Q", title="Goals scored"),
#             color=alt.condition(
#                 alt.datum.is_selected,
#                 alt.value("#B08D57"),  # bronze/gold - selected tournament
#                 alt.value("#D8CDB0"),  # muted parchment - other tournaments
#             ),
#             tooltip=[
#                 alt.Tooltip("year:O", title="Tournament"),
#                 alt.Tooltip("goals_scored:Q", title="Goals scored"),
#                 alt.Tooltip("goals_conceded:Q", title="Goals conceded"),
#                 alt.Tooltip("matches_played:Q", title="Matches"),
#             ],
#         )
#     )

#     labels = bars.mark_text(dy=-10, color="#2B3A2E", fontSize=13).encode(
#     text=alt.Text("goals_scored:Q")
# )

#     labels = bars.mark_text(dy=-10, color="#333", fontSize=13).encode(
#         text=alt.Text("goals_scored:Q")
#     )

#     st.altair_chart(bars + labels, use_container_width=True)

# st.divider()

# # --- Match table for the selected year ---
# st.subheader(f"Matches — {year}")

# matches_df = get_sa_matches_for_year(year)

# if matches_df.empty:
#     st.info(f"No South Africa matches loaded for {year}.")
# else:
#     st.dataframe(
#         format_matches_for_display(matches_df),
#         hide_index=True,
#         use_container_width=True,
#     )

# st.markdown("---")
# st.caption("© 2026 by uamahlecele.")