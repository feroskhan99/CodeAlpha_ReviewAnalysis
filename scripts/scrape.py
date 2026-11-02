"""
CodeAlpha Data Analytics Internship - Task 1: Web Scraping
Scrapes book data (title, category, price, rating, availability)
from https://books.toscrape.com (a practice site made for scraping).

Output: data/books.csv
Run:    python scripts/scrape.py
"""

import time
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://books.toscrape.com/"
DELAY = 0.5  # seconds between requests (be polite to the server)

RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

OUTPUT_FILE = Path(__file__).resolve().parent.parent / "data" / "books.csv"

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (CodeAlpha internship learning project)"})


def get_soup(url):
    """Download a page and return a BeautifulSoup object."""
    response = session.get(url, timeout=15)
    response.raise_for_status()
    response.encoding = "utf-8"  # fixes the 'Â£' symbol problem
    time.sleep(DELAY)
    return BeautifulSoup(response.text, "html.parser")


def get_categories():
    """Return a list of (category_name, category_url) from the sidebar."""
    soup = get_soup(BASE_URL)
    links = soup.select("div.side_categories ul li ul li a")
    return [(a.get_text(strip=True), urljoin(BASE_URL, a["href"])) for a in links]


def parse_book(article, category, page_url):
    """Extract data from one book block."""
    link = article.h3.a
    price_text = article.select_one("p.price_color").get_text(strip=True)
    rating_word = article.select_one("p.star-rating")["class"][1]

    return {
        "title": link["title"],
        "category": category,
        "price_gbp": float(price_text.replace("£", "")),
        "rating": RATING_MAP.get(rating_word),
        "availability": article.select_one("p.availability").get_text(strip=True),
        "url": urljoin(page_url, link["href"]),
    }


def scrape_category(name, url):
    """Scrape all pages of one category."""
    books = []
    while url:
        soup = get_soup(url)
        for article in soup.select("article.product_pod"):
            books.append(parse_book(article, name, url))
        next_btn = soup.select_one("li.next a")
        url = urljoin(url, next_btn["href"]) if next_btn else None
    return books


def main():
    categories = get_categories()
    print(f"Found {len(categories)} categories")

    all_books = []
    for i, (name, url) in enumerate(categories, start=1):
        try:
            books = scrape_category(name, url)
            all_books.extend(books)
            print(f"[{i}/{len(categories)}] {name}: {len(books)} books")
        except requests.RequestException as error:
            print(f"[{i}/{len(categories)}] {name}: FAILED ({error})")

    df = pd.DataFrame(all_books)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
    print(f"\nDone! Saved {len(df)} books to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
