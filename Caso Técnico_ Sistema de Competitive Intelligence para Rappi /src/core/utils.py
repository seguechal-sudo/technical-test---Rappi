import time
from datetime import datetime


def now() -> str:
    return datetime.now().isoformat()


def wait(t: float = 1) -> None:
    time.sleep(t)


def clear_and_type(locator, text: str) -> None:
    locator.click()
    wait(0.3)

    try:
        locator.press("Control+A")
        locator.press("Backspace")
    except Exception:
        pass

    try:
        locator.fill("")
    except Exception:
        pass

    locator.type(text, delay=12)