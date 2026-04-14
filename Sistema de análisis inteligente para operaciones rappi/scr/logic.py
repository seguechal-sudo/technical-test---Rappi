import re
import unicodedata
import pandas as pd
from scr.data import anomalies, bad_trends, get_latest_col


METRIC_MAP = {
    "lead penetration": "Lead Penetration",
    "perfect order": "Perfect Orders",
    "perfect orders": "Perfect Orders",
    "gross profit": "Gross Profit UE",
    "gross profit ue": "Gross Profit UE",
    "pro adoption": "Pro Adoption",
    "turbo adoption": "Turbo Adoption",
    "orders": "Orders",
    "mltv": "MLTV Top Verticals Adoption",
}

COUNTRY_MAP = {
    "mexico": "MX",
    "mx": "MX",
    "colombia": "CO",
    "co": "CO",
    "ecuador": "EC",
    "ec": "EC",
    "peru": "PE",
    "pe": "PE",
    "chile": "CL",
    "cl": "CL",
    "argentina": "AR",
    "ar": "AR",
    "brazil": "BR",
    "brasil": "BR",
    "br": "BR",
    "costa rica": "CR",
    "cr": "CR",
    "uruguay": "UY",
    "uy": "UY",
}


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
    return text


def extract_top_n(q: str, default: int = 5) -> int:
    match = re.search(r"\btop\s+(\d+)\b", q)
    if match:
        return int(match.group(1))
    match = re.search(r"\b(\d+)\b", q)
    if match:
        return int(match.group(1))
    return default


def extract_metric(q: str, available_metrics) -> str:
    qn = normalize_text(q)

    for alias, canonical in METRIC_MAP.items():
        if alias in qn and canonical in set(available_metrics):
            return canonical

    for metric in available_metrics:
        if normalize_text(metric) in qn:
            return metric

    return "Lead Penetration" if "Lead Penetration" in set(available_metrics) else list(available_metrics)[0]


def extract_country(q: str):
    qn = normalize_text(q)
    for alias, code in COUNTRY_MAP.items():
        if alias in qn:
            return code
    return None


def extract_zone(q: str, available_zones):
    qn = normalize_text(q)
    for zone in available_zones:
        if normalize_text(zone) in qn:
            return zone
    return None


def top_zones(df_metrics: pd.DataFrame, metric: str, n: int = 5, country: str = None) -> pd.DataFrame:
    latest_col = get_latest_col(df_metrics)
    df = df_metrics[df_metrics["METRIC"] == metric].copy()

    if country:
        df = df[df["COUNTRY"] == country]

    if df.empty:
        return pd.DataFrame()

    return df.sort_values(latest_col, ascending=False)[
        ["COUNTRY", "CITY", "ZONE", "ZONE_TYPE", latest_col]
    ].head(n)


def avg_by_country(df_long: pd.DataFrame, metric: str) -> pd.DataFrame:
    df = df_long[df_long["METRIC"] == metric].copy()
    if df.empty:
        return pd.DataFrame()

    return (
        df.groupby("COUNTRY", as_index=False)["VALUE"]
        .mean()
        .sort_values("VALUE", ascending=False)
    )


def trend(df_long: pd.DataFrame, metric: str, zone: str) -> pd.DataFrame:
    df = df_long[
        (df_long["METRIC"] == metric) &
        (df_long["ZONE"].str.lower() == zone.lower())
    ].copy()

    if df.empty:
        return pd.DataFrame()

    return df[["COUNTRY", "CITY", "ZONE", "METRIC", "WEEK", "VALUE"]].sort_values("WEEK")


def compare_wealth(df_metrics: pd.DataFrame, metric: str, country: str) -> pd.DataFrame:
    latest_col = get_latest_col(df_metrics)
    df = df_metrics[
        (df_metrics["METRIC"] == metric) &
        (df_metrics["COUNTRY"] == country)
    ].copy()

    if df.empty:
        return pd.DataFrame()

    return (
        df.groupby("ZONE_TYPE", as_index=False)[latest_col]
        .mean()
        .sort_values(latest_col, ascending=False)
    )


def multivariable(df_metrics: pd.DataFrame, metric1: str, metric2: str) -> pd.DataFrame:
    latest_col = get_latest_col(df_metrics)

    df1 = df_metrics[df_metrics["METRIC"] == metric1].copy()
    df2 = df_metrics[df_metrics["METRIC"] == metric2].copy()

    if df1.empty or df2.empty:
        return pd.DataFrame()

    merged = df1.merge(
        df2,
        on=["COUNTRY", "CITY", "ZONE"],
        suffixes=("_M1", "_M2")
    )

    m1_mean = merged[f"{latest_col}_M1"].mean()
    m2_mean = merged[f"{latest_col}_M2"].mean()

    out = merged[
        (merged[f"{latest_col}_M1"] > m1_mean) &
        (merged[f"{latest_col}_M2"] < m2_mean)
    ].copy()

    return out[[
        "COUNTRY", "CITY", "ZONE", f"{latest_col}_M1", f"{latest_col}_M2"
    ]].sort_values(f"{latest_col}_M1", ascending=False)


def problematic_zones(df_metrics: pd.DataFrame, df_long: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    latest_col = get_latest_col(df_metrics)

    base = df_metrics[["COUNTRY", "CITY", "ZONE", "ZONE_TYPE"]].drop_duplicates().copy()

    df_po = df_metrics[df_metrics["METRIC"] == "Perfect Orders"][
        ["COUNTRY", "CITY", "ZONE", latest_col]
    ].rename(columns={latest_col: "PERFECT_ORDERS_LATEST"})

    df_gp = df_metrics[df_metrics["METRIC"] == "Gross Profit UE"][
        ["COUNTRY", "CITY", "ZONE", latest_col]
    ].rename(columns={latest_col: "GROSS_PROFIT_LATEST"})

    anom = anomalies(df_long)
    negative_anom = anom[anom["CHANGE_PCT"] < 0].copy()
    negative_anom_count = (
        negative_anom.groupby(["COUNTRY", "CITY", "ZONE"])
        .size()
        .reset_index(name="NEGATIVE_ANOMALIES")
    )

    trends = bad_trends(df_long)
    if trends.empty:
        trend_count = pd.DataFrame(columns=["COUNTRY", "CITY", "ZONE", "NEGATIVE_TRENDS"])
    else:
        trend_count = (
            trends.groupby(["COUNTRY", "CITY", "ZONE"])
            .size()
            .reset_index(name="NEGATIVE_TRENDS")
        )

    result = base.merge(df_po, on=["COUNTRY", "CITY", "ZONE"], how="left")
    result = result.merge(df_gp, on=["COUNTRY", "CITY", "ZONE"], how="left")
    result = result.merge(negative_anom_count, on=["COUNTRY", "CITY", "ZONE"], how="left")
    result = result.merge(trend_count, on=["COUNTRY", "CITY", "ZONE"], how="left")

    result["NEGATIVE_ANOMALIES"] = result["NEGATIVE_ANOMALIES"].fillna(0)
    result["NEGATIVE_TRENDS"] = result["NEGATIVE_TRENDS"].fillna(0)

    po_mean = result["PERFECT_ORDERS_LATEST"].mean()
    gp_mean = result["GROSS_PROFIT_LATEST"].mean()

    result["PO_GAP"] = (po_mean - result["PERFECT_ORDERS_LATEST"]).fillna(0).clip(lower=0)
    result["GP_GAP"] = (gp_mean - result["GROSS_PROFIT_LATEST"]).fillna(0).clip(lower=0)

    result["PROBLEM_SCORE"] = (
        result["NEGATIVE_ANOMALIES"] * 3
        + result["NEGATIVE_TRENDS"] * 4
        + result["PO_GAP"]
        + result["GP_GAP"]
    )

    return result.sort_values("PROBLEM_SCORE", ascending=False)[[
        "COUNTRY", "CITY", "ZONE", "ZONE_TYPE",
        "NEGATIVE_ANOMALIES", "NEGATIVE_TRENDS",
        "PERFECT_ORDERS_LATEST", "GROSS_PROFIT_LATEST",
        "PROBLEM_SCORE"
    ]].head(n)


def order_growth_inference(df_orders: pd.DataFrame, df_metrics: pd.DataFrame, weeks: int = 5, n: int = 5) -> pd.DataFrame:
    if df_orders is None or df_orders.empty:
        return pd.DataFrame({"message": ["No se encontró dataset de órdenes"]})

    week_cols = [c for c in df_orders.columns if c.startswith("L") and "W" in c]
    if len(week_cols) < weeks:
        weeks = len(week_cols)

    ordered_weeks = sorted(
        week_cols,
        key=lambda x: int(re.search(r"L(\d+)W", x).group(1)),
        reverse=True
    )
    selected = ordered_weeks[-weeks:]  # últimas N hacia presente

    tmp = df_orders[["COUNTRY", "CITY", "ZONE"] + selected].copy()
    tmp["ORDER_GROWTH"] = tmp[selected[-1]] - tmp[selected[0]]
    tmp = tmp.sort_values("ORDER_GROWTH", ascending=False).head(n)

    latest_col = get_latest_col(df_metrics)

    lp = df_metrics[df_metrics["METRIC"] == "Lead Penetration"][["COUNTRY", "CITY", "ZONE", latest_col]].rename(
        columns={latest_col: "LEAD_PENETRATION"}
    )
    po = df_metrics[df_metrics["METRIC"] == "Perfect Orders"][["COUNTRY", "CITY", "ZONE", latest_col]].rename(
        columns={latest_col: "PERFECT_ORDERS"}
    )
    gp = df_metrics[df_metrics["METRIC"] == "Gross Profit UE"][["COUNTRY", "CITY", "ZONE", latest_col]].rename(
        columns={latest_col: "GROSS_PROFIT_UE"}
    )
    pa = df_metrics[df_metrics["METRIC"] == "Pro Adoption"][["COUNTRY", "CITY", "ZONE", latest_col]].rename(
        columns={latest_col: "PRO_ADOPTION"}
    )

    out = tmp.merge(lp, on=["COUNTRY", "CITY", "ZONE"], how="left")
    out = out.merge(po, on=["COUNTRY", "CITY", "ZONE"], how="left")
    out = out.merge(gp, on=["COUNTRY", "CITY", "ZONE"], how="left")
    out = out.merge(pa, on=["COUNTRY", "CITY", "ZONE"], how="left")

    def build_reason(row):
        reasons = []
        if pd.notna(row.get("LEAD_PENETRATION")):
            reasons.append(f"Lead Penetration={row['LEAD_PENETRATION']:.2f}")
        if pd.notna(row.get("PERFECT_ORDERS")):
            reasons.append(f"Perfect Orders={row['PERFECT_ORDERS']:.2f}")
        if pd.notna(row.get("GROSS_PROFIT_UE")):
            reasons.append(f"Gross Profit UE={row['GROSS_PROFIT_UE']:.2f}")
        if pd.notna(row.get("PRO_ADOPTION")):
            reasons.append(f"Pro Adoption={row['PRO_ADOPTION']:.2f}")
        return " | ".join(reasons)

    out["POSSIBLE_EXPLANATION"] = out.apply(build_reason, axis=1)

    return out[[
        "COUNTRY", "CITY", "ZONE", "ORDER_GROWTH",
        "LEAD_PENETRATION", "PERFECT_ORDERS", "GROSS_PROFIT_UE", "PRO_ADOPTION",
        "POSSIBLE_EXPLANATION"
    ]]