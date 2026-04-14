import pandas as pd
from scr.data import anomalies, bad_trends, correlations


def generate_anomalies(df_long):
    df = anomalies(df_long)
    return df.head(10)


def generate_bad_trends(df_long):
    df = bad_trends(df_long)
    return df.head(10)


def generate_correlations(df_long):
    return correlations(df_long)


def generate_opportunities(df_metrics):
    # simple pero válido para el caso
    latest_col = [c for c in df_metrics.columns if "L0W" in c][0]

    df_lp = df_metrics[df_metrics["METRIC"] == "Lead Penetration"]
    df_po = df_metrics[df_metrics["METRIC"] == "Perfect Orders"]

    merged = df_lp.merge(
        df_po,
        on=["COUNTRY", "CITY", "ZONE"],
        suffixes=("_LP", "_PO")
    )

    lp_mean = merged[f"{latest_col}_LP"].mean()
    po_mean = merged[f"{latest_col}_PO"].mean()

    return merged[
        (merged[f"{latest_col}_LP"] < lp_mean) &
        (merged[f"{latest_col}_PO"] > po_mean)
    ].head(10)


def generate_benchmark(df_metrics):
    latest_col = [c for c in df_metrics.columns if "L0W" in c][0]

    df = df_metrics[df_metrics["METRIC"] == "Lead Penetration"]

    return (
        df.groupby(["COUNTRY", "ZONE_TYPE"], as_index=False)[latest_col]
        .mean()
        .sort_values(latest_col, ascending=False)
    )