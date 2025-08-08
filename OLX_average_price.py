import requests
from bs4 import BeautifulSoup
import urllib.parse
import re
import statistics
import os
import random
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def get_soup(url):
    try:
        resp = requests.get(url, headers=HEADERS)
        if resp.status_code != 200:
            print(f"Помилка завантаження сторінки: {resp.status_code}")
            return None
        return BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        print(f"Помилка запиту: {e}")
        return None

def get_prices_and_links_from_url(url, pages=3, min_price=None, max_price=None):
    all_prices = []
    all_links = []
    for page in range(1, pages + 1):
        page_url = f"{url}?page={page}"
        print(f"Завантажую сторінку {page}...")
        soup = get_soup(page_url)
        if not soup:
            break
        listings = soup.select("div[data-testid='listing-grid'] div[data-cy='l-card']")
        if not listings:
            print("Оголошень більше не знайдено.")
            break

        for listing in listings:
            price_tag = listing.select_one("p[data-testid='ad-price']")
            link_tag = listing.find("a", href=True)
            if not price_tag or not link_tag:
                continue
            price_text = price_tag.get_text(strip=True)
            match = re.search(r"(\d[\d\s]*)", price_text.replace('\xa0', ' '))
            if match:
                price = int(match.group(1).replace(" ", ""))
                if (min_price is not None and price < min_price) or (max_price is not None and price > max_price):
                    continue
                link = "https://www.olx.ua" + link_tag['href'].split('#')[0]
                all_prices.append(price)
                all_links.append(link)

    return all_prices, all_links

def show_stats(prices):
    if not prices:
        print("Ціни не знайдено.")
        return None
    min_price = min(prices)
    max_price = max(prices)
    avg_price = round(statistics.mean(prices), 2)
    print(f"\nЗнайдено {len(prices)} цін:")
    print(f"Мінімальна ціна: {min_price} грн")
    print(f"Максимальна ціна: {max_price} грн")
    print(f"Середня ціна: {avg_price} грн")
    return avg_price, min_price, max_price

def save_results(subdir, filename, prices, links):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    directory = os.path.join(script_dir, subdir)
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, filename)
    with open(path, "w", encoding="utf-8") as f:
        for price, link in zip(prices, links):
            f.write(f"{price} грн | {link}\n")
    print(f"Збережено {len(prices)} результатів у {path}")

def print_results(prices, links):
    print("\nОголошення:")
    for i, (price, link) in enumerate(zip(prices, links), 1):
        print(f"{i}. {price} грн | {link}")

def input_price(prompt):
    while True:
        val = input(prompt).strip()
        if val == "":
            return None
        if val.isdigit():
            return int(val)
        print("Будь ласка, введіть число або залиште порожнім.")

def main():
    query = input("🔍 Введіть запит для пошуку на OLX (наприклад: iPhone 12): ").strip()
    if not query:
        print("Порожній запит. Завершення.")
        return

    encoded_query = urllib.parse.quote(query)
    search_url = f"https://www.olx.ua/uk/list/q-{encoded_query}/"

    prices, links = get_prices_and_links_from_url(search_url, pages=3)
    if not prices:
        print("Нічого не знайдено.")
        return

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    safe_query = re.sub(r"[^\w\d_-]", "_", query.lower())

    save_results("presearch", f"{safe_query}__{timestamp}.txt", prices, links)

    combined = list(zip(prices, links))
    if len(combined) > 20:
        combined = random.sample(combined, 20)
    sel_prices = [p for p, _ in combined]
    sel_links = [l for _, l in combined]

    show_stats(sel_prices)
    print_results(sel_prices, sel_links)

    while True:
        filter_answer = input("\nБажаєте задати фільтр ціни? (так/y/yes/ні/n/no): ").strip().lower()
        if filter_answer in ("так", "y", "yes"):
            min_price = input_price("Мінімальна ціна (Enter щоб пропустити): ")
            max_price = input_price("Максимальна ціна (Enter щоб пропустити): ")
            prices_f, links_f = get_prices_and_links_from_url(search_url, pages=3, min_price=min_price, max_price=max_price)
            if not prices_f:
                print("Оголошень у заданому діапазоні не знайдено.")
                continue

            combined_f = list(zip(prices_f, links_f))
            if len(combined_f) > 20:
                combined_f = random.sample(combined_f, 20)
            sel_prices_f = [p for p, _ in combined_f]
            sel_links_f = [l for _, l in combined_f]

            show_stats(sel_prices_f)
            print_results(sel_prices_f, sel_links_f)
            save_results("results", f"{safe_query}__filtered__{timestamp}.txt", sel_prices_f, sel_links_f)
            break

        elif filter_answer in ("ні", "n", "no"):
            print("Фільтр не застосовано.")
            save_results("results", f"{safe_query}__{timestamp}.txt", sel_prices, sel_links)
            break
        else:
            print("Відповідь не розпізнана. Введіть так або ні.")

if __name__ == "__main__":
    main()
