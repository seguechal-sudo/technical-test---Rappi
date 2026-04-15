from __future__ import annotations
import pandas as pd


def _safe_float(value):
    try:
        if pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


def build_metrics_summary(df: pd.DataFrame) -> dict:
    total_rows = len(df)

    success_df = df[df["status"].astype(str).str.lower() == "success"].copy()
    failed_df = df[df["status"].astype(str).str.lower() != "success"].copy()

    success_count = len(success_df)
    failed_count = len(failed_df)
    success_rate = (success_count / total_rows * 100) if total_rows else 0.0

    platform_summary = (
        success_df.groupby("platform", dropna=False)
        .agg(
            registros=("platform", "count"),
            precio_promedio=("price", "mean"),
            eta_promedio=("eta", "mean"),
            descuentos=("active_discount", lambda x: x.notna().sum()),
        )
        .reset_index()
        .to_dict(orient="records")
        if not success_df.empty
        else []
    )

    store_summary = (
        success_df.groupby("store", dropna=False)
        .agg(
            registros=("store", "count"),
            precio_promedio=("price", "mean"),
            eta_promedio=("eta", "mean"),
        )
        .reset_index()
        .sort_values("precio_promedio", ascending=False)
        .to_dict(orient="records")
        if not success_df.empty
        else []
    )

    product_summary = (
        success_df.groupby(["product", "platform"], dropna=False)
        .agg(
            registros=("product", "count"),
            precio_promedio=("price", "mean"),
            eta_promedio=("eta", "mean"),
        )
        .reset_index()
        .sort_values(["product", "precio_promedio"], ascending=[True, False])
        .to_dict(orient="records")
        if not success_df.empty
        else []
    )

    address_summary = (
        success_df.groupby("address", dropna=False)
        .agg(
            registros=("address", "count"),
            precio_promedio=("price", "mean"),
            eta_promedio=("eta", "mean"),
        )
        .reset_index()
        .sort_values("eta_promedio", ascending=False)
        .to_dict(orient="records")
        if not success_df.empty
        else []
    )

    return {
        "total_rows": total_rows,
        "success_count": success_count,
        "failed_count": failed_count,
        "success_rate": success_rate,
        "platforms": sorted(success_df["platform"].dropna().astype(str).unique().tolist()),
        "stores": sorted(success_df["store"].dropna().astype(str).unique().tolist()),
        "products": sorted(success_df["product"].dropna().astype(str).unique().tolist()),
        "unique_addresses": int(success_df["address"].dropna().astype(str).nunique()) if not success_df.empty else 0,
        "avg_price": _safe_float(success_df["price"].mean()) if not success_df.empty else None,
        "min_price": _safe_float(success_df["price"].min()) if not success_df.empty else None,
        "max_price": _safe_float(success_df["price"].max()) if not success_df.empty else None,
        "avg_eta": _safe_float(success_df["eta"].mean()) if not success_df.empty else None,
        "min_eta": _safe_float(success_df["eta"].min()) if not success_df.empty else None,
        "max_eta": _safe_float(success_df["eta"].max()) if not success_df.empty else None,
        "discount_count": int(success_df["active_discount"].notna().sum()) if not success_df.empty else 0,
        "platform_summary": platform_summary,
        "store_summary": store_summary,
        "product_summary": product_summary,
        "address_summary": address_summary,
        "top_errors": (
            failed_df["error"].fillna("unknown").value_counts().head(10).to_dict()
            if not failed_df.empty
            else {}
        ),
    }