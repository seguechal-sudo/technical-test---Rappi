import json
import os
import pandas as pd


def load_addresses(filepath: str):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"No existe {filepath}")
    return pd.read_csv(filepath).to_dict("records")


def load_products(filepath: str):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"No existe {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_row(row: dict, output_path: str):
    df = pd.DataFrame([row])
    if os.path.exists(output_path):
        df.to_csv(output_path, mode="a", header=False, index=False)
    else:
        df.to_csv(output_path, index=False)