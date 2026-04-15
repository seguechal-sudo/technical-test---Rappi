import json
import re

from src.core.utils import wait, clear_and_type, now
from src.core.parsers import parse_money, parse_eta, extract_first_text
from src.core.selectors import PRICE_SELECTORS, ETA_SELECTORS, DISCOUNT_SELECTORS


def set_address(page, address):
    page.goto("https://www.ubereats.com/mx", timeout=60000, wait_until="domcontentloaded")
    wait(2)

    trigger_selectors = [
        'button:has-text("Selecciona tu ubicación")',
        'button:has-text("Ingresa tu dirección")',
        'button:has-text("Dirección")',
        'button:has-text("Ubicación")'
    ]

    for sel in trigger_selectors:
        try:
            loc = page.locator(sel)
            if loc.count():
                loc.first.click(timeout=4000)
                wait(1)
                break
        except Exception:
            continue

    input_selectors = [
        'input[placeholder*="dirección"]',
        'input[placeholder*="Dirección"]',
        'input[placeholder*="address"]',
        'input[placeholder*="Address"]',
        'input[placeholder*="entrega"]',
        'input[placeholder*="Entrega"]',
        'input[type="text"]',
        'input[type="search"]'
    ]

    typed = False
    for sel in input_selectors:
        try:
            loc = page.locator(sel)
            if loc.count():
                first = loc.first
                if not first.is_visible():
                    continue
                clear_and_type(first, address)
                wait(2)
                typed = True
                break
        except Exception:
            continue

    if not typed:
        return False

    suggestion_selectors = [
        '[role="option"]',
        '[aria-selected]',
        'li',
        'button'
    ]

    for sel in suggestion_selectors:
        try:
            loc = page.locator(sel)
            count = loc.count()
            if count == 0:
                continue

            for i in range(min(count, 6)):
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

    try:
        page.keyboard.press("ArrowDown")
        wait(0.5)
        page.keyboard.press("Enter")
        wait(2)
        return True
    except Exception:
        return False


def search_store(page, store):
    selectors = [
        'input[data-testid="search-input"]',
        'input[placeholder*="Buscar"]',
        'input[placeholder*="Search"]',
        'input[aria-label*="Buscar"]',
        'input[aria-label*="Search"]',
        'input[type="search"]'
    ]

    for sel in selectors:
        try:
            loc = page.locator(sel)
            if loc.count():
                first = loc.first
                if not first.is_visible():
                    continue
                clear_and_type(first, store)
                wait(1.5)
                return True
        except Exception:
            continue
    return False


def open_first_store(page):
    selectors = [
        '[data-testid="search-suggestion-result-store"] a',
        'li[data-testid="search-suggestion-result-store"] a',
        '#search-suggestions-typeahead-menu li[data-testid="search-suggestion-result-store"] a',
        '#search-suggestions-typeahead-menu li[role="option"] a',
        'a[data-testid="store-card"]',
        'div[data-testid="store-card"] a',
        'a[href*="/mx/store/"]'
    ]

    for sel in selectors:
        try:
            page.wait_for_selector(sel, timeout=5000)
            loc = page.locator(sel)
            if loc.count():
                loc.first.click(timeout=5000)
                wait(3)
                return True
        except Exception:
            continue
    return False


def extract_product_from_json(page, product_name):
    script_selectors = ['script[type="application/ld+json"]']

    for sel in script_selectors:
        try:
            scripts = page.locator(sel)
            count = scripts.count()

            for i in range(count):
                raw = scripts.nth(i).inner_text()
                if not raw:
                    continue

                try:
                    data = json.loads(raw)
                except Exception:
                    continue

                if not isinstance(data, dict):
                    continue

                menu = data.get("hasMenu", {})
                sections = menu.get("hasMenuSection", [])

                if not sections:
                    continue

                for section in sections:
                    if isinstance(section, dict):
                        section = [section]

                    for sec in section:
                        section_name = sec.get("name")
                        items = sec.get("hasMenuItem", [])

                        for item in items:
                            if isinstance(item, dict):
                                item = [item]

                            for prod in item:
                                name = prod.get("name", "")
                                price = prod.get("offers", {}).get("price")

                                if product_name.lower() in name.lower():
                                    return {
                                        "found": True,
                                        "matched_product_name": name,
                                        "matched_section_name": section_name,
                                        "price": parse_money(price),
                                        "price_text": f"${price}" if price is not None else None,
                                    }
        except Exception:
            continue

    return {"found": False}


def close_blocking_popup(page):
    selectors = [
        'button[aria-label*="Cerrar"]',
        'button[aria-label*="close"]',
        'button:has-text("Cerrar")',
        'button:has-text("Close")',
        'button:has-text("Entendido")',
        'button:has-text("Ahora no")',
        'button:has-text("No, gracias")',
        'button:has-text("Not now")',
        '[role="dialog"] button[aria-label*="Cerrar"]',
        '[role="dialog"] button[aria-label*="close"]',
        '[role="dialog"] button',
        '[aria-modal="true"] button'
    ]

    closed = False

    for sel in selectors:
        try:
            loc = page.locator(sel)
            count = loc.count()
            if count == 0:
                continue

            for i in range(min(count, 5)):
                try:
                    btn = loc.nth(i)
                    if btn.is_visible():
                        text = ""
                        aria = ""

                        try:
                            text = btn.inner_text().strip().lower()
                        except Exception:
                            pass

                        try:
                            aria = (btn.get_attribute("aria-label") or "").strip().lower()
                        except Exception:
                            pass

                        if (
                            "cerrar" in text or "close" in text or "entendido" in text
                            or "ahora no" in text or "no, gracias" in text
                            or "not now" in text or "cerrar" in aria or "close" in aria
                        ):
                            btn.click(timeout=3000)
                            wait(1.5)
                            closed = True
                except Exception:
                    continue
        except Exception:
            continue

    try:
        page.keyboard.press("Escape")
        wait(0.5)
    except Exception:
        pass

    return closed


def open_product_in_page(page, product_name):
    selectors = [
        f'[data-testid*="product"]:has-text("{product_name}")',
        f'[role="button"]:has-text("{product_name}")',
        f'[role="link"]:has-text("{product_name}")',
        f'button:has-text("{product_name}")',
        f'a:has-text("{product_name}")',
        f'text="{product_name}"',
        f'text=/{re.escape(product_name)}/i'
    ]

    for _ in range(8):
        close_blocking_popup(page)

        for sel in selectors:
            try:
                loc = page.locator(sel)
                count = loc.count()
                if count == 0:
                    continue

                for i in range(min(count, 10)):
                    try:
                        item = loc.nth(i)
                        if item.is_visible():
                            item.scroll_into_view_if_needed(timeout=3000)
                            wait(0.5)

                            try:
                                item.click(timeout=5000)
                                wait(2)
                                return True
                            except Exception:
                                close_blocking_popup(page)
                                wait(1)
                                item.click(timeout=5000)
                                wait(2)
                                return True
                    except Exception:
                        continue
            except Exception:
                continue

        try:
            page.mouse.wheel(0, 1800)
            wait(1.5)
        except Exception:
            break

    return False


def extract_metrics(page):
    return {
        "price": parse_money(extract_first_text(page, PRICE_SELECTORS)),
        "eta": parse_eta(extract_first_text(page, ETA_SELECTORS)),
        "active_discount": extract_first_text(page, DISCOUNT_SELECTORS)
    }


def scrape(page, address, product):
    row = {
        "timestamp": now(),
        "platform": "Uber Eats",
        "address": address,
        "store": product["store_name"],
        "product": product["product_name"],
        "matched_product_name": None,
        "matched_section_name": None,
        "price": None,
        "price_text": None,
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

        if not open_first_store(page):
            row["error"] = "store_first_option_open"
            return row

        json_result = extract_product_from_json(page, product["product_name"])

        if not json_result.get("found"):
            row["error"] = "product_not_found_in_json"
            return row

        row["matched_product_name"] = json_result.get("matched_product_name")
        row["matched_section_name"] = json_result.get("matched_section_name")
        row["price"] = json_result.get("price")
        row["price_text"] = json_result.get("price_text")

        close_blocking_popup(page)

        if not open_product_in_page(page, json_result["matched_product_name"]):
            row["error"] = "product_not_found_in_page"
            return row

        ui_metrics = extract_metrics(page)
        row["eta"] = ui_metrics.get("eta")
        row["active_discount"] = ui_metrics.get("active_discount")
        row["status"] = "success"
        return row

    except Exception as e:
        row["error"] = str(e)
        return row