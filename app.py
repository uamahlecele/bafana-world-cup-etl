import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(page_title="iBafana Bafana & the World Cup", layout="wide")

DB_PATH = "bafana_bafana_wc.db"
RSA_ID = "43883"  # FIFA numeric ID

SA_QUERY = """SELECT
    m.year,
    m.date,
    m.stage,
    CASE WHEN m.home_team_id = '43883' THEN at.name ELSE ht.name END AS opponent,
    CASE
        WHEN m.winner_id = '43883' THEN 'Win'
        WHEN m.winner_id IS NULL OR m.winner_id = '' THEN 'Draw'
        ELSE 'Loss'
    END AS result,
    CASE WHEN m.home_team_id = '43883' THEN m.home_score ELSE m.away_score END AS sa_score,
    CASE WHEN m.home_team_id = '43883' THEN m.away_score ELSE m.home_score END AS opponent_score
FROM matches AS m
LEFT JOIN teams AS ht
       ON m.home_team_id = ht.id_team AND m.year = ht.year
LEFT JOIN teams AS at
       ON m.away_team_id = at.id_team AND m.year = at.year
WHERE m.home_team_id = '43883'
   OR m.away_team_id = '43883'
ORDER BY m.date;"""

@st.cache_data
def get_sa_matches():
    connect = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(SA_QUERY, connect)
    connect.close()
    return df


st.title("Bafana Bafana's All Time Performance at the FIFA World Cup")

st.dataframe(get_sa_matches())

st.markdown(
    "Tracking South Africa's Football Team performance in the FIFA World Cup "
    "from their debut in 1998 onwards."
)


st.markdown("---")
st.caption("© 2026 by uamahlecele.")