from pathlib import Path
import pandas as pd


def load_competitive_data(filepath: str) -> pd.DataFrame:
    """
    Carga un archivo CSV o Excel y normaliza columnas esperadas.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {filepath}")

    suffix = path.suffix.lower()

    if suffix == ".csv":
        df = pd.read_csv(path)
    elif suffix in {".xlsx", ".xls"}:
        df = pd.read_excel(path)
    else:
        raise ValueError("Formato no soportado. Usa .csv, .xlsx o .xls")

    expected_cols = [
        "timestamp",
        "platform",
        "address",
        "store",
        "product",
        "matched_product_name",
        "matched_section_name",
        "price",
        "price_text",
        "eta",
        "active_discount",
        "status",
        "error",
    ]

    for col in expected_cols:
        if col not in df.columns:
            df[col] = None

    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["eta"] = pd.to_numeric(df["eta"], errors="coerce")

    return df