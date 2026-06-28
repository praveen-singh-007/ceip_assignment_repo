"""Generate the three demo datasets used by the 5 use cases in the project brief.

Run once with: python data/generate_sample_data.py
Deliberately injects some messiness (nulls, duplicates, an outlier) into the
sales dataset so the Data Quality Audit use case has something real to find.
"""

import os

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
HERE = os.path.dirname(os.path.abspath(__file__))


def make_sales() -> pd.DataFrame:
    regions = ["North", "South", "East", "West"]
    products = ["Widget A", "Widget B", "Gadget X", "Gadget Y", "Gizmo Z"]
    categories = {"Widget A": "Widgets", "Widget B": "Widgets", "Gadget X": "Gadgets",
                  "Gadget Y": "Gadgets", "Gizmo Z": "Gizmos"}

    dates = pd.date_range("2025-01-01", "2025-06-30", freq="D")
    rows = []
    for _ in range(450):
        date = rng.choice(dates)
        region = rng.choice(regions, p=[0.35, 0.25, 0.2, 0.2])
        product = rng.choice(products)
        units = int(rng.integers(1, 50))
        unit_price = round(float(rng.uniform(8, 120)), 2)
        revenue = round(units * unit_price, 2)
        rows.append(
            {
                "date": pd.Timestamp(date).strftime("%Y-%m-%d"),
                "region": region,
                "product": product,
                "category": categories[product],
                "units_sold": units,
                "unit_price": unit_price,
                "revenue": revenue,
                "customer_id": f"C{int(rng.integers(1000, 1200))}",
            }
        )

    df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)

    # Inject realistic messiness for the Data Quality Audit use case.
    null_idx = rng.choice(df.index, size=12, replace=False)
    df.loc[null_idx[:6], "revenue"] = np.nan
    df.loc[null_idx[6:], "units_sold"] = np.nan

    outlier_idx = rng.choice(df.index, size=2, replace=False)
    df.loc[outlier_idx, "revenue"] = df.loc[outlier_idx, "revenue"] * 25

    dup_rows = df.sample(4, random_state=1)
    df = pd.concat([df, dup_rows], ignore_index=True)

    return df


def make_traffic() -> pd.DataFrame:
    dates = pd.date_range("2024-07-01", "2025-06-30", freq="D")
    n = len(dates)
    trend = np.linspace(800, 2400, n)
    weekly_season = 200 * np.sin(np.arange(n) * (2 * np.pi / 7))
    noise = rng.normal(0, 120, n)
    sessions = np.clip(trend + weekly_season + noise, 50, None).round().astype(int)
    sources = rng.choice(["Organic", "Paid", "Referral", "Direct", "Social"], size=n,
                          p=[0.4, 0.2, 0.15, 0.15, 0.1])

    return pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "sessions": sessions, "source": sources})


def make_customers() -> pd.DataFrame:
    n = 300
    signup_dates = pd.to_datetime("2023-01-01") + pd.to_timedelta(
        rng.integers(0, 700, size=n), unit="D"
    )
    total_spend = rng.gamma(shape=2.0, scale=180, size=n).round(2)
    num_orders = rng.poisson(lam=total_spend / 120 + 1, size=n)
    last_active = signup_dates + pd.to_timedelta(rng.integers(0, 720, size=n), unit="D")
    channel = rng.choice(["Email", "Ads", "Organic", "Referral"], size=n, p=[0.3, 0.3, 0.25, 0.15])

    return pd.DataFrame(
        {
            "customer_id": [f"CUST{i:04d}" for i in range(1, n + 1)],
            "signup_date": signup_dates.strftime("%Y-%m-%d"),
            "total_spend": total_spend,
            "num_orders": num_orders,
            "last_active_date": last_active.strftime("%Y-%m-%d"),
            "channel": channel,
        }
    )


if __name__ == "__main__":
    make_sales().to_csv(os.path.join(HERE, "sample_sales.csv"), index=False)
    make_traffic().to_csv(os.path.join(HERE, "sample_traffic.csv"), index=False)
    make_customers().to_csv(os.path.join(HERE, "sample_customers.csv"), index=False)
    print("Wrote sample_sales.csv, sample_traffic.csv, sample_customers.csv")
