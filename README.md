# iBafana Bafana & the FIFA World Cup

Tracking South Africa's national football team's performance and stats at
the FIFA World Cup, from their debut in 1998 onwards.

## What this project does

This is an end-to-end ETL pipeline that pulls FIFA World Cup team and match data (primarily focusing on iBafana Bafana's journey)
from multiple sources, cleans and normalizes it into a single schema, and
loads it into a shared SQLite database — with a Streamlit dashboard on top
for exploring the data. 

**Tournaments covered:** 1998, 2002, 2010, 2026

**Data sources:**
- 2026 — extracted live from the FIFA API
- 1998 / 2002 / 2010 — extracted from historical CSV data
  ([`stiles/world-cup`](https://github.com/stiles/world-cup) on GitHub)

## Why these tournaments

1998 was South Africa's World Cup debut. 2010 was the tournament they
hosted. 2026 is the most recent edition. Together they trace the arc of
Bafana Bafana's World Cup history.

## Tech stack

- **Python** — `requests` for API extraction, `csv`/`pandas` for file-based
  extraction
- **SQLite** — storage
- **Streamlit** — interactive dashboard for exploring stats by year

## What I learnt

This project was my first time building a real ETL build end-to-end. My first time utilising streamlit which I found to be a very cool library.


WTC-BQT5V5VX

