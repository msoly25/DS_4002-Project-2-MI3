
"""
Script: 02_debt_trends.py
Project: U.S. Federal Student Debt Analysis

Purpose:
    Analyze historical changes in federal student debt,
    calculate year-over-year growth rates, and generate
    descriptive figures and a results table.

Input:
    DATA/portfolio_clean.csv

Outputs:
    OUTPUT/debt_growth_rates.csv
    OUTPUT/debt_over_time.png
    OUTPUT/debt_yoy_growth.png

Required packages:
    pandas, matplotlib
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# 1. Set file paths relative to the project root
ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "DATA" / "portfolio_clean.csv"
OUTPUT_DIR = ROOT / "OUTPUT"

OUTPUT_DIR.mkdir(exist_ok=True)

# 2. Load cleaned student debt data
df = pd.read_csv(DATA_FILE, parse_dates=["period_end"])
df = df.sort_values("period_end").reset_index(drop=True)

# 3. Calculate year-over-year debt changes
# Match observations to the same date one year earlier.
# This accounts for the combination of annual and
# quarterly reporting periods in the dataset.

debt_by_date = df.set_index("period_end")[
    "total_debt_billions"
]

previous_dates = df["period_end"] - pd.DateOffset(years=1)
previous_debt = previous_dates.map(debt_by_date)

df["yoy_change_billions"] = (
    df["total_debt_billions"] - previous_debt
)

df["yoy_growth_pct"] = (
    df["yoy_change_billions"] / previous_debt
) * 100

# 4. Save the growth rate results
results = df[
    [
        "fiscal_year",
        "quarter",
        "period_end",
        "total_debt_billions",
        "yoy_change_billions",
        "yoy_growth_pct",
    ]
]

results.to_csv(
    OUTPUT_DIR / "debt_growth_rates.csv",
    index=False
)

# 5. Plot total federal student debt over time
plt.figure(figsize=(10, 5))

plt.plot(
    df["period_end"],
    df["total_debt_billions"],
    marker="o",
    markersize=3
)

plt.title("Total U.S. Federal Student Debt Over Time")
plt.xlabel("Reporting Date")
plt.ylabel("Outstanding Debt ($ Billions)")
plt.grid(alpha=0.3)
plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "debt_over_time.png",
    dpi=300
)
plt.close()

# 6. Plot year-over-year debt growth rates
growth = df.dropna(subset=["yoy_growth_pct"])

plt.figure(figsize=(10, 5))

plt.plot(
    growth["period_end"],
    growth["yoy_growth_pct"],
    marker="o",
    markersize=3
)

plt.axhline(0, color="black", linestyle="--")
plt.title("Year-over-Year Federal Student Debt Growth")
plt.xlabel("Reporting Date")
plt.ylabel("Year-over-Year Growth (%)")
plt.grid(alpha=0.3)
plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "debt_yoy_growth.png",
    dpi=300
)
plt.close()

# 7. Display summary results
print("Debt trend analysis completed.")

print("\nFirst total debt value ($ billions):")
print(df["total_debt_billions"].iloc[0])

print("\nLast total debt value ($ billions):")
print(df["total_debt_billions"].iloc[-1])

print("\nTotal debt increase ($ billions):")
print(
    df["total_debt_billions"].iloc[-1]
    - df["total_debt_billions"].iloc[0]
)

print("\nOutput files saved in:")
print(OUTPUT_DIR)
