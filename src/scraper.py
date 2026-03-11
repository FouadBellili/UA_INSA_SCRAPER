import logging
import pathlib
import time

from playwright.sync_api import sync_playwright, Page

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

BASE_DIR = pathlib.Path(__file__).parent.parent
BRONZE_DIR = BASE_DIR / "data" / "bronze"


def scrape_page(page: Page, url: str, file_path: pathlib.Path):
    """Visit a URL and save its HTML."""
    try:
        page.goto(url, timeout=15000)
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(page.content())
        logging.info(f"Saved: {url} → {file_path.name}")
    except Exception as e:
        logging.error(f"Error on {url}: {e}")


def get_ua_article_links(page: Page) -> list[str]:
    """Paginate through all news and collect article links."""
    while page.get_by_role("button", name="Carregar mais").is_visible():
        try:
            page.get_by_role("button", name="Carregar mais").click(timeout=5000)
            page.wait_for_load_state("networkidle")
            time.sleep(5)
        except Exception as e:
            logging.error(f"[UA] Error clicking 'Carregar mais': {e}")
            break

    links = page.eval_on_selector_all(
        "a[href*='/pt/noticias/3/']",
        "elements => [...new Set(elements.map(el => el.href))]"
    )
    logging.info(f"[UA] Found {len(links)} article links")
    return links


def scrape_ua(page: Page):
    """Scrape all news articles from Universidade de Aveiro."""
    logging.info("Starting Universidade de Aveiro scrape")
    articles_dir = BRONZE_DIR / "ua_news"
    articles_dir.mkdir(parents=True, exist_ok=True)

    try:
        page.goto("https://www.ua.pt/pt/noticias/3")
        page.wait_for_load_state("networkidle")
    except Exception as e:
        logging.error(f"[UA] Failed to navigate to main page: {e}")
        return

    links = get_ua_article_links(page)

    for i, url in enumerate(links, start=1):
        scrape_page(page, url, articles_dir / f"article_{i:04d}.html")

    logging.info(f"[UA] {len(links)} articles saved to {articles_dir}")


def get_insa_job_links(page: Page) -> list[str]:
    """Collect all job offer links from the INSA listing page."""
    links = page.eval_on_selector_all(
        "a[href*='/insa-rouen-normandie/offres-demploi/']",
        """elements => [...new Set(
            elements
                .map(el => el.href)
                .filter(href => !href.endsWith('/offres-demploi/offre-emploi'))
        )]"""
    )
    logging.info(f"[INSA] Found {len(links)} job offer links")
    return links


def scrape_insa(page: Page):
    """Scrape all job offers from INSA Rouen."""
    logging.info("Starting INSA Rouen scrape")
    jobs_dir = BRONZE_DIR / "insa_jobs"
    jobs_dir.mkdir(parents=True, exist_ok=True)

    try:
        page.goto("https://www.insa-rouen.fr/insa-rouen-normandie/offres-demploi")
        page.wait_for_load_state("networkidle")
    except Exception as e:
        logging.error(f"[INSA] Failed to navigate to job listing page: {e}")
        return

    links = get_insa_job_links(page)

    for i, url in enumerate(links, start=1):
        scrape_page(page, url, jobs_dir / f"job_{i:04d}.html")

    logging.info(f"[INSA] {len(links)} job offers saved to {jobs_dir}")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        scrape_ua(page)
        scrape_insa(page)

        browser.close()
        logging.info("All scraping complete.")

