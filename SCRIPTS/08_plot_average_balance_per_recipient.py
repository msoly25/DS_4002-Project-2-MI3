"""
Script: 08_plot_average_balance_per_recipient.py
Project: U.S. Federal Student Debt Analysis

Purpose:
    Plot average outstanding balances by loan program and overall.

Input:
    DATA/portfolio_clean.csv

Output:
    OUTPUT/Average Outstanding Balance per Recipient.png

Required packages:
    pandas, matplotlib
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


# Locate files relative to the repository, regardless of the current directory.
ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "DATA" / "portfolio_clean.csv"
OUTPUT_FILE = ROOT / "OUTPUT" / "Average Outstanding Balance per Recipient.png"
OUTPUT_FILE.parent.mkdir(exist_ok=True)

# Load and order the cleaned data.
df = pd.read_csv(DATA_FILE, parse_dates=["period_end"])
df = df.sort_values("period_end")

# Plot program-level and overall average outstanding balances.
fig, ax = plt.subplots(figsize=(14, 8))
ax.plot(
    df["period_end"],
    df["direct_avg_balance_thousands"],
    label="Direct Loans",
)
ax.plot(
    df["period_end"],
    df["ffel_avg_balance_thousands"],
    label="FFEL",
)
ax.plot(
    df["period_end"],
    df["perkins_avg_balance_thousands"],
    label="Perkins",
)
ax.plot(
    df["period_end"],
    df["total_avg_balance_thousands"],
    label="Total Average",
    color="red",
    linestyle="--",
    linewidth=2.5,
)

ax.set_title("Average Outstanding Balance per Recipient")
ax.set_xlabel("Reporting Date")
ax.set_ylabel("Average Balance ($ Thousands)")
ax.legend()
ax.grid(True, alpha=0.3)
fig.autofmt_xdate()
fig.tight_layout()

fig.savefig(OUTPUT_FILE, dpi=300)
plt.close(fig)

print("Average-balance plot saved to:")
print(OUTPUT_FILE)
