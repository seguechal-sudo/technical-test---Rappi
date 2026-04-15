import re


def parse_money(text):
    if text is None:
        return None
    if isinstance(text, (int, float)):
        return float(text)

    match = re.search(r"(\d+(?:\.\d+)?)", str(text).replace(",", ""))
    return float(match.group(1)) if match else None


def parse_eta(text):
    if not text:
        return None

    nums = re.findall(r"\d+", str(text))
    return sum(map(int, nums)) / len(nums) if nums else None


def extract_first_text(page, selectors):
    for sel in selectors:
        try:
            loc = page.locator(sel)
            if loc.count() > 0:
                txt = loc.first.inner_text().strip()
                if txt:
                    return txt
        except Exception:
            continue
    return None