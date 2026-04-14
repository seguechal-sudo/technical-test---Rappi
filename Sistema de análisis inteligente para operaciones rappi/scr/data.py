import re
import pandas as pd


def _detect_week_cols(df: pd.DataFrame):
    return [col for col in df.columns if col.startswith("L") and "W" in col]


def _sort_week_labels(labels):
    def extract_week_num(label):
        match = re.search(r"L(\d+)W", str(label))
        if not match:
            return 999
        return int(match.group(1))
    return sorted(labels, key=extract_week_num, reverse=True)


def _build_long(df: pd.DataFrame, id_vars):
    week_cols = _detect_week_cols(df)
    if not week_cols:
        raise ValueError("No se encontraron columnas de semanas")

    df_long = df.melt(
        id_vars=id_vars,
        value_vars=week_cols,
        var_name="WEEK",
        value_name="VALUE"
    )

    week_order = _sort_week_labels(df_long["WEEK"].unique())
    df_long["WEEK"] = pd.Categorical(df_long["WEEK"], categories=week_order, ordered=True)

    return df_long.sort_values(id_vars + ["WEEK"]).reset_index(drop=True)


def get_latest_col(df: pd.DataFrame) -> str:
    for col in ["L0W_VALUE", "L0W", "L0W_ROLL"]:
        if col in df.columns:
            return col

    week_cols = _detect_week_cols(df)
    if not week_cols:
        raise ValueError("No se encontró columna de última semana")
    ordered = _sort_week_labels(week_cols)
    return ordered[-1]


def load_data(path: str):
    """
    Retorna:
    - df_metrics
    - df_metrics_long
    - df_orders
    - df_orders_long
    """
    xls = pd.ExcelFile(path)

    if len(xls.sheet_names) < 1:
        raise ValueError("El archivo no tiene hojas válidas")

    df_metrics = pd.read_excel(path, sheet_name=0)

    required_metrics_cols = [
        "COUNTRY", "CITY", "ZONE", "ZONE_TYPE", "ZONE_PRIORITIZATION", "METRIC"
    ]
    missing_metrics = [c for c in required_metrics_cols if c not in df_metrics.columns]
    if missing_metrics:
        raise ValueError(f"Faltan columnas en métricas: {missing_metrics}")

    df_metrics_long = _build_long(df_metrics, required_metrics_cols)

    df_orders = None
    df_orders_long = None

    if len(xls.sheet_names) >= 2:
        df_orders = pd.read_excel(path, sheet_name=1)

        required_orders_cols = ["COUNTRY", "CITY", "ZONE", "METRIC"]
        missing_orders = [c for c in required_orders_cols if c not in df_orders.columns]
        if not missing_orders:
            df_orders_long = _build_long(df_orders, required_orders_cols)

    print("\nHojas detectadas:", xls.sheet_names)
    print("Columnas métricas:", df_metrics.columns.tolist())
    if df_orders is not None:
        print("Columnas órdenes:", df_orders.columns.tolist())

    print(f"\nFilas métricas: {len(df_metrics)}")
    print(f"Filas métricas long: {len(df_metrics_long)}")
    if df_orders is not None:
        print(f"Filas órdenes: {len(df_orders)}")
    if df_orders_long is not None:
        print(f"Filas órdenes long: {len(df_orders_long)}")

    return df_metrics, df_metrics_long, df_orders, df_orders_long


def anomalies(df_long: pd.DataFrame) -> pd.DataFrame:
    df = df_long.copy()
    df = df.sort_values(["COUNTRY", "CITY", "ZONE", "METRIC", "WEEK"])
    df["PREV_VALUE"] = df.groupby(["COUNTRY", "CITY", "ZONE", "METRIC"])["VALUE"].shift(1)
    df["CHANGE_PCT"] = ((df["VALUE"] - df["PREV_VALUE"]) / df["PREV_VALUE"]) * 100
    out = df[df["PREV_VALUE"].notna() & (df["CHANGE_PCT"].abs() > 10)].copy()
    return out.sort_values("CHANGE_PCT")


def bad_trends(df_long: pd.DataFrame) -> pd.DataFrame:
    rows = []
    grouped = df_long.groupby(["COUNTRY", "CITY", "ZONE", "METRIC"])

    for (country, city, zone, metric), sub in grouped:
        sub = sub.sort_values("WEEK")
        values = sub["VALUE"].tolist()
        if len(values) >= 3:
            last3 = values[-3:]
            if last3[0] > last3[1] > last3[2]:
                rows.append({
                    "COUNTRY": country,
                    "CITY": city,
                    "ZONE": zone,
                    "METRIC": metric,
                    "LAST_3_VALUES": last3,
                    "TREND": "Consistent deterioration"
                })

    return pd.DataFrame(rows)


def correlations(df_long: pd.DataFrame) -> pd.DataFrame:
    pivot = df_long.pivot_table(
        index=["COUNTRY", "CITY", "ZONE"],
        columns="METRIC",
        values="VALUE",
        aggfunc="mean"
    )
    return pivot.corr(numeric_only=True)