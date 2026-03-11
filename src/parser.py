from bs4 import BeautifulSoup
import logging
import pathlib
import sqlite3

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

BASE_DIR = pathlib.Path(__file__).parent.parent
BRONZE_DIR = BASE_DIR / "data" / "bronze"
SILVER_DIR = BASE_DIR / "data" / "silver"
UA_DIR = BRONZE_DIR / "ua_news"
INSA_DIR = BRONZE_DIR / "insa_jobs"
DB_PATH = SILVER_DIR / "jobs_and_news.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def extract_ua_article(file: pathlib.Path) -> dict | None:
    """Extract fields from a UA news article page."""
    with open(file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    canonical = soup.find("link", rel="canonical")
    url = canonical["href"] if canonical else None

    # Title: <p class="sc-VigVT hIhIhv">
    title_tag = soup.find("p", class_="hIhIhv")
    title = title_tag.get_text(strip=True) if title_tag else None

    # Date: <p class="sc-VigVT hBdxXc">
    date_tag = soup.find("p", class_="hBdxXc")
    date = date_tag.get_text(strip=True) if date_tag else None

    # Short description: <p class="sc-VigVT eNJsUb">
    desc_tag = soup.find("p", class_="eNJsUb")
    description = desc_tag.get_text(strip=True) if desc_tag else None

    # Full body: <div class="markdown">
    body_tag = soup.find("div", class_="markdown")
    body = body_tag.get_text(separator=" ", strip=True) if body_tag else None

    return {
        "source": "ua",
        "title": title,
        "date": date,
        "description": description,
        "body": body,
        "url": url,
    }


def extract_insa_job(file: pathlib.Path) -> dict | None:
    """Extract fields from an INSA Rouen job offer page."""
    with open(file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    canonical = soup.find("link", rel="canonical")
    url = canonical["href"] if canonical else None

    # Title
    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else None

    # Opening / closing dates
    intro = soup.find("div", class_="offre-d-emploi__field-introduction")
    date = intro.get_text(separator=" | ", strip=True)[:300] if intro else None

    # Full description
    content = soup.find("div", class_="field-content")
    body = content.get_text(separator=" ", strip=True) if content else None

    return {
        "source": "insa",
        "title": title,
        "date": date,
        "description": None,  # INSA pages have no short description
        "body": body,
        "url": url,
    }


def init_db(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            source      TEXT NOT NULL,
            title       TEXT,
            date        TEXT,
            description TEXT,
            body        TEXT,
            url         TEXT UNIQUE
        )
    """)
    conn.commit()


def insert_item(conn: sqlite3.Connection, item: dict):
    try:
        conn.execute(
            """INSERT INTO items (source, title, date, description, body, url)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (item["source"], item["title"], item["date"],
             item["description"], item["body"], item["url"])
        )
    except sqlite3.IntegrityError:
        logging.warning(f"Duplicate skipped: {item['url']}")


def process():
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    ua_files = list(UA_DIR.glob("*.html"))
    insa_files = list(INSA_DIR.glob("*.html"))
    logging.info(f"Processing {len(ua_files)} UA articles and {len(insa_files)} INSA job offers")

    for file in ua_files:
        item = extract_ua_article(file)
        if item:
            insert_item(conn, item)

    for file in insa_files:
        item = extract_insa_job(file)
        if item:
            insert_item(conn, item)

    conn.commit()
    conn.close()
    logging.info(f"Data stored in {DB_PATH}")


if __name__ == "__main__":
    process()