def main():
    from src.scraper import scrape_ua_news
    from src.parser import extract_data, store_data_in_db
    from src.analyzer import analyze_news_data

    results = analyze_news_data()
    for key, value in results.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
