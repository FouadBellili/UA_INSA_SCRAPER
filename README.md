# UA Grant News Scraper

A web scraping and text analysis pipeline that collects grant announcements from the University of Aveiro (UA) news portal, extracts structured information, and makes them easily searchable.

---

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Setup](#setup)
- [Usage](#usage)
- [Pipeline Architecture](#pipeline-architecture)
- [Modules](#modules)
- [Database Schema](#database-schema)
- [CLI Reference](#cli-reference)

---

## Overview

This project automates the collection and analysis of grant announcements published on the [UA News Portal](https://www.ua.pt/pt/noticias/3). It:

1. Scrapes JavaScript-rendered pages using Playwright
2. Stores raw HTML in a local bronze layer
3. Parses and stores structured data in SQLite
4. Extracts deadlines, funding amounts, emails, and phone numbers using regex patterns
5. Provides a CLI for searching, filtering, and exporting grants

---

## Project Structure

```
ua-grant-scraper/
├── data/
│   └── bronze/
│       └── ua_news/
│           ├── page_1.html        # Raw paginated listing pages
│           ├── articles/
│           │   ├── article_0001.html
│           │   └── ...
│           └── grants.db          # SQLite database
├── src/
│   ├── scraper.py                 # Web scraper (Playwright)
│   ├── parser.py                  # HTML parser & DB storage
│   ├── text_analysis.py           # Pattern extraction & keyword search
│   ├── migrate_db.py              # DB migration (add missing columns)
│   ├── export.py                  # CSV / JSON export
│   └── cli.py                     # CLI entrypoint
├── pyproject.toml
├── .python-version
└── README.md
```

---

## Setup

### Requirements

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/ua-grant-scraper.git
cd ua-grant-scraper

# Create virtual environment and install dependencies
uv sync

# Install Playwright browsers
uv run playwright install chromium
```

### Dependencies (`pyproject.toml`)

```toml
[project]
dependencies = [
    "playwright",
    "beautifulsoup4",
    "lxml",
    "rich",          # CLI formatting
]
```

---

## Usage

### Run the full pipeline manually

```bash
# 1. Scrape all grant pages and save raw HTML
uv run python src/scraper.py

# 2. Run DB migration (adds metadata columns if missing)
uv run python src/migrate_db.py

# 3. Parse HTML and populate the database
uv run python src/parser.py

# 4. Run text analysis (extract deadlines, amounts, contacts)
uv run python src/text_analysis.py
```

### CLI

```bash
# Scrape latest grants
uv run python src/cli.py scrape

# Search grants by keyword
uv run python src/cli.py search "bolsa doutoramento"

# Filter by upcoming deadlines (next 30 days)
uv run python src/cli.py deadlines --days 30

# Export to CSV or JSON
uv run python src/cli.py export --format csv
uv run python src/cli.py export --format json

# Show database statistics
uv run python src/cli.py stats
```

---

## Pipeline Architecture

```
UA News Portal
      │
      ▼
[ scraper.py ]  ──►  data/bronze/ua_news/
  Playwright             Raw HTML files
  Pagination
  Article pages
      │
      ▼
[ parser.py ]   ──►  grants.db (SQLite)
  BeautifulSoup          title, date,
  Structured data        description, url
      │
      ▼
[ text_analysis.py ] ─► grants.db (metadata columns)
  Regex patterns          deadlines, amounts,
  Normalization           emails, phones
      │
      ▼
[ cli.py / export.py ]
  Search, filter,
  CSV / JSON export
```

---

## Modules

### `scraper.py`

Handles JavaScript-rendered content via Playwright.

- Navigates to `https://www.ua.pt/pt/noticias/3`
- Clicks "Carregar mais" until all listings are loaded
- Saves each paginated listing as `page_N.html`
- Collects all article URLs matching `/pt/noticias/3/XXXXX`
- Saves each article page as `article_NNNN.html`

### `parser.py`

Parses raw HTML and stores structured data in SQLite.

- Extracts title, publication date, description, source URL, and attachment links
- Cleans HTML entities and normalizes encoding
- Implements idempotent inserts (skips duplicates by URL)

### `text_analysis.py`

Extracts metadata from article text using pattern matching.

| Function | Description |
|---|---|
| `extract_deadlines()` | Finds dates near Portuguese trigger words (prazo, candidaturas até…) |
| `extract_funding_amounts()` | Matches euro amounts with context (bolsa, dotação, financiamento…) |
| `extract_emails()` | Standard email regex |
| `extract_phone_numbers()` | Portuguese landlines and mobiles (+351 prefix optional) |
| `normalize_text()` | Lowercase + remove accents for search |
| `search_grants()` | Keyword search across all grants (accent-insensitive) |
| `filter_by_deadline()` | Filter grants by upcoming deadline range |

### `migrate_db.py`

Safe migration script — adds metadata columns to the `grants` table only if they don't already exist. Safe to run multiple times.

```bash
uv run python src/migrate_db.py
```

### `export.py`

Exports all grants to CSV or JSON.

```python
export_to_csv("data/grants.csv")
export_to_json("data/grants.json")
```

---

## Database Schema

```sql
CREATE TABLE grants (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    title              TEXT NOT NULL,
    publication_date   TEXT,
    description        TEXT,
    source_url         TEXT UNIQUE,
    attachment_links   TEXT,          -- JSON array

    -- Metadata (populated by text_analysis.py)
    earliest_deadline  TEXT,          -- ISO date: 2025-06-30
    deadlines          TEXT,          -- JSON array of ISO dates
    funding_amounts    TEXT,          -- JSON array of raw strings
    emails             TEXT,          -- JSON array
    phone_numbers      TEXT,          -- JSON array
    normalized_text    TEXT           -- accent-free lowercase for search
);
```

---

## CLI Reference

| Command | Description |
|---|---|
| `scrape` | Run the scraper manually |
| `search <term>` | Search grants by keyword (accent-insensitive) |
| `deadlines [--days N]` | Show grants with deadlines in the next N days (default: all upcoming) |
| `export [--format csv\|json]` | Export all grants to file |
| `stats` | Show total grants, date range, and extraction coverage |

---

## Notes

- Raw HTML files are kept in the bronze layer and are never deleted, allowing re-parsing without re-scraping.
- The scraper uses `time.sleep()` between requests to avoid overloading the server.
- Text analysis patterns are tuned for Portuguese-language content.
