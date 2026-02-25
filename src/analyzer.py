import sqlite3
import re
import pathlib

BASE_DIR = pathlib.Path(__file__).parent.parent
SILVER_DIR = BASE_DIR / "data" / "silver" / "ua_news"
SILVER_DIR.mkdir(parents=True, exist_ok=True)

def analyze_news_data(silver_dir=SILVER_DIR):
    conn = sqlite3.connect(silver_dir / "ua_news.db")
    cursor = conn.cursor()

    cursor.execute("SELECT title, description FROM news")
    rows = cursor.fetchall()
    fundings = []
    emails = []
    phone_numbers = []
    deadlines = []
    for title, description in rows:
