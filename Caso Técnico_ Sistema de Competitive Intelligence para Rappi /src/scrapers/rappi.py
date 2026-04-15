import json
import re
from urllib.parse import quote_plus

from src.core.utils import wait, clear_and_type, now
from src.core.parsers import parse_money, parse_eta, extract_first_text
from src.core.selectors import PRICE_SELECTORS, ETA_SELECTORS, DISCOUNT_SELECTORS


def click_confirm_address(page):
    selectors = [
        '#confirm-address-button',
        '[data-qa="confirm-address"]',
        'button[aria-label="Confirmar Dirección"]',
        'button:has-text("Confirmar dirección")',
        'button:has-text("Confirmar Dirección")'
    ]

    for sel in selectors:
        try:
            btn = page.locator(sel)
            if btn.count():
                btn.first.click(timeout=5000)
                wait(2)
                return True
        except Exception:
            continue
    return False


def click_save_address(page):
    selectors = [
        '#save-address-button',
        'button[aria-label="Guardar dirección"]',
        'button:has-text("Guardar dirección")',
        'button:has-text("Guardar Dirección")'
    ]

    for sel in selectors:
        try:
            btn = page.locator(sel)
            if btn.count():
                btn.first.click(timeout=5000)
                wait(2)
                return True
        except Exception:
            continue
    return False


def open_address_modal(page):
    trigger_selectors = [
        '.ButtonAddress__text',
        '[class*="ButtonAddress"]',
        '[data-testid*="address"]',
        'button:has-text("dirección")',
        'div:has-text("dirección")',
        'text=/Ingresa tu dirección/i',
        'text=/dirección/i'
    ]

    for sel in trigger_selectors:
        try:
            loc = page.locator(sel)
            if loc.count():
                loc.first.click(timeout=4000)
                break
        except Exception:
            continue

    try:
        page.wait_for_selector('[data-qa="address-modal"]', timeout=6000)
        wait(1)
        return True
    except Exception:
        return False


def get_address_modal(page):
    return page.locator('[data-qa="address-modal"]').first


def type_address(page, address):
    modal = get_address_modal(page)

    input_selectors = [
        'input[placeholder*="dirección"]',
        'input[placeholder*="Dirección"]',
        'input[aria-label*="dirección"]',
        'input[aria-label*="Dirección"]',
        'input[placeholder*="address"]',
        'input[type="search"]',
        'input[type="text"]'
    ]

    for sel in input_selectors:
        try:
            loc = modal.locator(sel)
            if loc.count():
                first = loc.first
                if not first.is_visible():
                    continue
                clear_and_type(first, address)
                wait(2)
                return True
        except Exception:
            continue

    return False


def select_suggestion(page, address):
    modal = get_address_modal(page)
    address_head = address.split(",")[0].strip().lower()

    suggestion_selectors = [
        '[role="option"]',
        '[aria-selected]',
        '[data-testid*="address"]',
        '[data-qa*="address"]',
        'li',
        'button'
    ]

    wait(2)

    for sel in suggestion_selectors:
        try:
            loc = modal.locator(sel)
            count = loc.count()
            if count == 0:
                continue

            for i in range(min(count, 10)):
                try:
                    item = loc.nth(i)
                    if not item.is_visible():
                        continue

                    txt = item.inner_text().strip().lower()
                    if not txt:
                        continue

                    if (
                        address_head in txt
                        or "méxico" in txt
                        or "mexico" in txt
                        or "victoria" in txt
                        or "tamps" in txt
                    ):
                        item.click(timeout=5000)
                        wait(2)
                        return True
                except Exception:
                    continue
        except Exception:
            continue

    for sel in suggestion_selectors:
        try:
            loc = modal.locator(sel)
            count = loc.count()
            if count == 0:
                continue

            for i in range(min(count, 5)):
                try:
                    item = loc.nth(i)
                    if item.is_visible():
                        item.click(timeout=5000)
                        wait(2)
                        return True
                except Exception:
                    continue
        except Exception:
            continue

    return False


def set_address(page, address):
    page.goto("https://www.rappi.com.mx", timeout=60000, wait_until="domcontentloaded")
    wait(2)

    if not open_address_modal(page):
        return False

    if not type_address(page, address):
        return False

    selected = select_suggestion(page, address)

    if not selected:
        try:
            page.keyboard.press("ArrowDown")
            wait(0.5)
            page.keyboard.press("Enter")
            wait(2)
        except Exception:
            return False

    if not click_confirm_address(page):
        return False

    click_save_address(page)
    wait(2)
    return True


def search_store(page, store):
    url = f"https://www.rappi.com.mx/search?store_type=all&query={quote_plus(store)}"
    page.goto(url, timeout=60000, wait_until="domcontentloaded")
    wait(2)
    return True


def open_store(page, store):
    selectors = [
        f'a:has-text("{store}")',
        f'[role="link"]:has-text("{store}")',
        f'[data-testid*="store"]:has-text("{store}")',
        f'[data-testid*="merchant"]:has-text("{store}")',
        f'text="{store}"',
        f'text=/{re.escape(store)}/i'
    ]

    for sel in selectors:
        try:
            loc = page.locator(sel)
            if loc.count():
                loc.first.click(timeout=5000)
                wait(3)
                return True
        except Exception:
            continue

    return False


def extract_product_from_json(page, product):
    try:
        script = page.locator('#seo-structured-schema').inner_text()
        data = json.loads(script)
        sections = data.get("hasMenu", {}).get("hasMenuSection", [])

        for group in sections:
            if isinstance(group, dict):
                group = [group]

            for section in group:
                items_groups = section.get("hasMenuItem", [])

                for items in items_groups:
                    if isinstance(items, dict):
                        items = [items]

                    for item in items:
                        name = item.get("name", "").lower()
                        if product.lower() in name:
                            return {
                                "price": parse_money(item["offers"]["price"]),
                                "matched_product_name": item.get("name"),
                                "matched_section_name": section.get("name"),
                                "status": "success"
                            }

        return {"status": "not_found"}
    except Exception:
        return {"status": "error"}


def extract_metrics(page):
    return {
        "price": parse_money(extract_first_text(page, PRICE_SELECTORS)),
        "eta": parse_eta(extract_first_text(page, ETA_SELECTORS)),
        "active_discount": extract_first_text(page, DISCOUNT_SELECTORS)
    }


def search_product_dom(page, product):
    selectors = [
        'input[placeholder*="Buscar"]',
        'input[placeholder*="buscar"]',
        'input[aria-label*="Buscar"]',
        'input[type="search"]'
    ]

    for sel in selectors:
        try:
            loc = page.locator(sel)
            if loc.count():
                first = loc.first
                if not first.is_visible():
                    continue
                clear_and_type(first, product)
                wait(1)
                page.keyboard.press("Enter")
                wait(2)
                return True
        except Exception:
            continue
    return False


def open_product_dom(page, product):
    selectors = [
        f'text="{product}"',
        f'[data-testid*="product"]:has-text("{product}")',
        f'[role="button"]:has-text("{product}")',
        f'[role="link"]:has-text("{product}")',
        f'text=/{re.escape(product)}/i'
    ]

    for sel in selectors:
        try:
            loc = page.locator(sel)
            if loc.count():
                loc.first.click(timeout=5000)
                wait(2)
                return True
        except Exception:
            continue
    return False


def scrape(page, address, product):
    row = {
        "timestamp": now(),
        "platform": "Rappi",
        "address": address,
        "store": product["store_name"],
        "product": product["product_name"],
        "matched_product_name": None,
        "matched_section_name": None,
        "price": None,
        "eta": None,
        "active_discount": None,
        "status": "failed",
        "error": None
    }

    try:
        if not set_address(page, address):
            row["error"] = "address"
            return row

        if not search_store(page, product["store_name"]):
            row["error"] = "store_search"
            return row

        if not open_store(page, product["store_name"]):
            row["error"] = "store_open"
            return row

        result = extract_product_from_json(page, product["product_name"])

        if result["status"] == "success":
            row.update(result)
            row.update(extract_metrics(page))
            row["price"] = result.get("price") or row.get("price")
            row["status"] = "success"
            return row

        search_product_dom(page, product["product_name"])
        open_product_dom(page, product["product_name"])
        row.update(extract_metrics(page))
        row["status"] = "success"
        return row

    except Exception as e:
        row["error"] = str(e)
        return row