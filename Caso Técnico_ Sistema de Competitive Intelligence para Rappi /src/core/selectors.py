PRICE_SELECTORS = [
    "text=/MX\\$\\s*\\d+/",
    "text=/\\$\\s*\\d+/",
    "text=/\\d+[\\.,]?\\d*\\s*MXN/"
]

ETA_SELECTORS = [
    "text=/\\d+\\s*-\\s*\\d+\\s*min/i",
    "text=/\\d+\\s*min/i"
]

DISCOUNT_SELECTORS = [
    "text=/\\d+%\\s*OFF/i",
    "text=/\\d+%/i",
    "text=/descuento/i",
    "text=/promo/i",
    "text=/promoción/i",
    "text=/cupón/i",
    "text=/ahorra/i",
    "text=/envío gratis/i"
]