from playwright.sync_api import sync_playwright

from src.config import OUTPUT, ADDRESSES_FILE, PRODUCTS_FILE, PLATFORMS
from src.core.io import load_addresses, load_products, save_row
from src.core.utils import wait
from src.scrapers import rappi, uber


def run():
    addresses = load_addresses(ADDRESSES_FILE)
    products = load_products(PRODUCTS_FILE)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=200)
        context = browser.new_context()

        for plat in PLATFORMS:
            for addr in addresses:
                for prod in products:
                    page = context.new_page()

                    print(f"{plat['name']} | {prod['store_name']} | {prod['product_name']}")

                    if plat["name"] == "Rappi":
                        result = rappi.scrape(page, addr["address"], prod)
                    else:
                        result = uber.scrape(page, addr["address"], prod)

                    save_row(result, OUTPUT)
                    page.close()
                    wait(1)

        browser.close()