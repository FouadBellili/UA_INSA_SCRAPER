def main():
    from src.scraper import main as scrape_data
    from src.parser import extract_data, store_data_in_db
    from src.analyzer import analyze_news_data

    scrape_data()

if __name__ == "__main__":
    main()
